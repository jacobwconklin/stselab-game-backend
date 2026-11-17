"""Response regression and query-count checks; uses only a disposable SQLite DB."""
import json
from pathlib import Path
import unittest

from verify import BackendAdapter


FIXTURE=Path(__file__).parent/"fixtures/session_responses_before_batching.json"
ENDPOINTS=("players","roundresults","finalresults","armroundresults",
           "armfinalresults","surveyssubmitted")


def insert(db,table,**values):
    columns=", ".join(values)
    placeholders=", ".join("?" for _ in values)
    db.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",tuple(values.values()))


def seed_mixed_records(db):
    for session in (111111,222222,333333):
        insert(db,"Session",JoinCode=session,Round=6)
    for index,name in enumerate(("Ada", "O'Brien", "Zoë", None)):
        insert(db,"PlayerBrief",Id=f"player-{index}",Name=name,
               Color=None if index==3 else "#112233",SessionId=111111)
    insert(db,"PlayerBrief",Id="outsider",Name="Other session",SessionId=222222)
    insert(db,"PlayerBrief",Id="departed",Name="Left session",SessionId=None)

    # Existing behavior treats any dice record, including offboarding, as completion.
    for player,onboarding in (("player-1",0),("player-2",1),("player-2",0),
                              ("outsider",1),("departed",1)):
        insert(db,"DiceResult",PlayerId=player,Onboarding=onboarding)
    for player in ("player-1","player-1","player-3","outsider","departed"):
        insert(db,"FreeRoamSurvey",PlayerId=player,Drive=1)

    for player,round_number,shots,score in (
        ("player-1",1,4,10),("player-1",3,5,20),
        ("player-1",6,6,30),("player-1",9,9,90),("player-1",7,7,40),
        ("player-2",6,8,50),("player-2",6,99,99),("player-2",9,9,60),
        ("player-3",6,None,0),("outsider",6,100,100),("departed",6,100,100)):
        insert(db,"RoundResult",PlayerId=player,Round=round_number,Shots=shots,
               Cost=0,Score=score,SolverOne=1,SolverTwo=None,SolverThree=3,
               Architecture="h",CustomPerformanceWeight=None)
    for player,round_number,weight,score in (
        ("player-1",12,100,10),("player-1",15,150,30),("player-1",13,110,20),
        ("player-2",12,200,40),("player-2",12,999,99),("player-2",15,220,50),
        ("player-3",12,None,0),("outsider",12,999,99),("departed",12,999,99)):
        insert(db,"ArmRoundResult",PlayerId=player,Round=round_number,Grams=weight,
               Cost=0,Score=score,SolverOne=1,SolverTwo=None,SolverThree=3,
               SolverFour=None,Architecture="Manipulator and Grabber")
    db.commit()


def response_cases():
    for endpoint in ENDPOINTS:
        payload={"sessionId":111111}
        if endpoint=="roundresults":
            payload["round"]=6
        elif endpoint=="armroundresults":
            payload["round"]=12
        yield endpoint,payload
    for endpoint,round_number in (("roundresults",1),("roundresults",8),
                                  ("armroundresults",13),("armroundresults",14)):
        yield endpoint,{"sessionId":111111,"round":round_number}
    for session in (333333,999999):
        for endpoint in ENDPOINTS:
            payload={"sessionId":session}
            if endpoint in ("roundresults","armroundresults"):
                payload["round"]=6 if endpoint=="roundresults" else 12
            yield endpoint,payload


class BatchedQueryTests(unittest.TestCase):
    def setUp(self):
        self.backend=BackendAdapter()
        self.client=self.backend.app.test_client()

    def tearDown(self):
        self.backend.close()

    def test_responses_match_original_handlers(self):
        seed_mixed_records(self.backend.db)
        fixtures=json.loads(FIXTURE.read_text(encoding="utf-8"))
        for case in fixtures["cases"]:
            with self.subTest(endpoint=case["endpoint"],payload=case["payload"]):
                response=self.client.post("/session/"+case["endpoint"],json=case["payload"])
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.get_json(),case["response"])

    def test_query_count_is_constant_at_one_five_one_hundred_and_five_hundred_players(self):
        for count in (1,5,100,500):
            with self.subTest(players=count):
                self.backend.db.executescript("DELETE FROM PlayerBrief; DELETE FROM Session;")
                insert(self.backend.db,"Session",JoinCode=111111,Round=6)
                for index in range(count):
                    insert(self.backend.db,"PlayerBrief",Id=f"player-{index}",
                           Name=f"Player {index}",SessionId=111111)
                self.backend.db.commit()
                for endpoint in ENDPOINTS:
                    self.backend.queries.clear()
                    response=self.client.post("/session/"+endpoint,
                                              json={"sessionId":111111,"round":6})
                    body=response.get_json()
                    self.assertTrue(body.get("success"),body)
                    self.assertEqual(len(self.backend.queries),3 if endpoint=="players" else 2,
                                     f"{endpoint} with {count} players")
                    if endpoint=="surveyssubmitted":
                        self.assertEqual(body["totalPlayers"],count)
                        self.assertEqual(body["surveysSubmitted"],0)
                    else:
                        self.assertEqual(len(body["players" if endpoint=="players" else "results"]),count)

    def test_bulk_lookups_use_bound_parameters_for_player_ids_and_rounds(self):
        insert(self.backend.db,"Session",JoinCode=111111,Round=6)
        player_id="player'quoted"
        insert(self.backend.db,"PlayerBrief",Id=player_id,SessionId=111111)
        insert(self.backend.db,"RoundResult",PlayerId=player_id,Round=6,Shots=7,
               Cost=8,Architecture="h",Score=9)
        insert(self.backend.db,"ArmRoundResult",PlayerId=player_id,Round=12,Grams=7,
               Cost=8,Architecture="h",Score=9)
        insert(self.backend.db,"DiceResult",PlayerId=player_id,Onboarding=1)
        insert(self.backend.db,"FreeRoamSurvey",PlayerId=player_id,Drive=1)
        for endpoint in ENDPOINTS:
            with self.subTest(endpoint=endpoint):
                self.backend.queries.clear()
                round_number=12 if endpoint=="armroundresults" else 6
                body=self.client.post("/session/"+endpoint,
                                      json={"sessionId":111111,"round":round_number}).get_json()
                self.assertTrue(body.get("success"),body)
                sql,parameters=self.backend.queries[-1]
                self.assertNotIn(player_id,sql)
                self.assertIn(player_id,parameters)
                if endpoint=="surveyssubmitted":
                    self.assertEqual(body["surveysSubmitted"],1)
                elif endpoint=="players":
                    self.assertEqual(body["completedOnboarding"],[player_id])
                else:
                    result=body["results"][0]
                    score=result["scores"][0] if "scores" in result else result
                    self.assertEqual(score["score"],9)

    def test_grouping_uses_roster_ids_with_case_insensitive_matching(self):
        # Model MySQL's possible case-insensitive ID comparison explicitly.
        self.backend.db.executescript("""
            DROP TABLE PlayerBrief;
            CREATE TABLE PlayerBrief (
                Id TEXT COLLATE NOCASE PRIMARY KEY, Name TEXT, Color TEXT, SessionId INTEGER
            );
        """)
        insert(self.backend.db,"Session",JoinCode=111111,Round=6)
        insert(self.backend.db,"PlayerBrief",Id="player-lower",SessionId=111111)
        insert(self.backend.db,"RoundResult",PlayerId="PLAYER-LOWER",Round=6,
               Shots=7,Cost=8,Architecture="h",Score=9)
        insert(self.backend.db,"ArmRoundResult",PlayerId="PLAYER-LOWER",Round=12,
               Grams=7,Cost=8,Architecture="h",Score=9)
        insert(self.backend.db,"DiceResult",PlayerId="PLAYER-LOWER",Onboarding=1)
        insert(self.backend.db,"FreeRoamSurvey",PlayerId="PLAYER-LOWER",Drive=1)
        for endpoint in ENDPOINTS:
            with self.subTest(endpoint=endpoint):
                body=self.client.post("/session/"+endpoint,json={
                    "sessionId":111111,"round":12 if endpoint=="armroundresults" else 6
                }).get_json()
                self.assertTrue(body.get("success"),body)
                if endpoint=="players":
                    self.assertEqual(body["completedOnboarding"],["player-lower"])
                elif endpoint=="surveyssubmitted":
                    self.assertEqual(body["surveysSubmitted"],1)
                else:
                    result=body["results"][0]
                    self.assertEqual(result["id"],"player-lower")
                    score=result["scores"][0] if "scores" in result else result
                    self.assertEqual(score["score"],9)


if __name__=="__main__":
    unittest.main(verbosity=2)
