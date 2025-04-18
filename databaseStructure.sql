-- SQL database structure and commands for instantiating database, querying database, etc. 

-- Session Table:
CREATE TABLE Session (
    JoinCode int PRIMARY KEY,
    Round int NULL,
    StartDate datetime,
    EndDate datetime
);

-- Player Brief Table:
CREATE TABLE PlayerBrief (
    Id varchar(255) PRIMARY KEY,
    Name varchar(255),
    Color varchar(255),
    SessionId int,
    FOREIGN KEY (SessionId) REFERENCES session(JoinCode)
)

-- Player Information Table:
CREATE TABLE PlayerInformation (
    Id varchar(255) PRIMARY KEY,
    Name varchar(255),
    ParticipationReason varchar(255),
    Gender varchar(255),
    Age int,
    Residence varchar(255), -- Changed from country to Residence
    Ethnicity varchar(255), -- Deleted Hobbies and added Ethnicity (taken from Stanford: https://idealdeisurvey.stanford.edu/frequently-asked-questions/survey-definitions)
    IsCollegeStudent bit,
    University varchar(255),
    DegreeProgram varchar(255),
    YearsInProgram int,
    -- each education field will now be prefaced with "yes" or "current" to tell if person is actively a student or not.
    -- removed associates and proffesional educations
    HighSchoolEducation varchar(255),
    BachelorsEducation varchar(255),
    MastersEducation varchar(255), 
    DoctorateEducation varchar(255),
    OtherEducation varchar(255),
    OtherEducationName varchar(255),

    -- Removed specializations and added new 7 point experience questions:
    RiskAnalysisExperience int,
    SupplierExperience int,
    ProposalOrStatementOfWorkExperience int,
    bidsForRequestsExperience int,
    systemArchitectureExperience int,
    golfExperience int,

    SystemsEngineeringExpertise int,
    StatementOfWorkExpertise int
)

-- If there is only a value for SolverOne and not SolverTwo and SolverThree and if the round is 1 or 2 
-- then h_arch was used.
-- If there is only values for SolverOne and SolverTwo and not SolverThree and if the round is 3 then
-- lp_arch was used.
-- If there are values for SolverOne, SolverTwo, and SolverThree and if the round is 4 then dap_arch was used.
-- Solver are ints where: 1 -> Professional, 2 -> Amatuer, 3 -> Specialist
-- Custom Performance Weight is an int between 20 and 80 that represents the percent of the score that is 
-- associated with performance. 100 - Custom Performance Weight is the percent of the score that is associated 
-- with cost. This value is chosen by the player
-- Round Result Table:
CREATE TABLE RoundResult (
    Id int AUTO_INCREMENT PRIMARY KEY,
    Round int,
    Shots int,
    Cost int,
    SolverOne int,
    SolverTwo int,
    SolverThree int,
    PlayerId varchar(255), 
    FOREIGN KEY (PlayerId) REFERENCES PlayerBrief(Id),
    Architecture varchar(255),
    Score int,
    CustomPerformanceWeight int,
    Reasoning varchar(255)
)

-- Free Roam Result from expiremental playground
-- Solver are ints where: 1 -> Professional, 2 -> Amatuer, 3 -> Specialist
-- Modules are ints where 1 -> Drive, 2 -> Long, 3 -> Fairway, 4 -> Short, 5 -> Putt
CREATE TABLE FreeRoamResult (
    Id int AUTO_INCREMENT PRIMARY KEY,
    Shots int,
    Distance int,
    Solver int,
    Module int,
    PlayerId varchar(255),
    FOREIGN KEY (PlayerId) REFERENCES PlayerBrief(Id)
)

-- Free Roam Survey Results for players to choose the best solver for each module.
-- The number stored per module is for a solver as an int that can represent multiple solvers as follows:
-- 1 -> Professional
-- 2 -> Amateur
-- 3 -> Specialist
-- 4 -> Professional and Amateur
-- 5 -> Professional and Specialist
-- 6 -> Amateur and Specialist
-- 7 -> Professional, Amateur, and Specialist (could be stored in 3 bits!)
CREATE TABLE FreeRoamSurvey (
    Id int AUTO_INCREMENT PRIMARY KEY,
    Drive int,
    LongChoice int,
    Fairway int,
    Short int,
    Putt int,
    EntireHole int,
    PlayerId varchar(255), 
    FOREIGN KEY (PlayerId) REFERENCES PlayerBrief(Id)
)

-- Saves results of D&D inspired dice picking for Onboarding and Offboarding game
-- Save number of each kind of dice, save playerID, save if it was Onboarding or Offboarding, 
-- and save their score (probability of rolling 12 0r 20)
CREATE TABLE DiceResult (
    Id int AUTO_INCREMENT PRIMARY KEY,
    D6 int,
    D8 int,
    D10 int,
    D12 int,
    D20 int,
    PlayerId varchar(255),
    FOREIGN KEY (PlayerId) REFERENCES PlayerBrief(Id),
    Onboarding bit,
    Score DECIMAL(4,2),
    Reasoning varchar(255),
    FinalReasoning varchar(240)
)

-- Queries for saving csv files beyond selecting all per table:

-- Gives player details, survey choices, and dice results for a given session
SELECT PlayerInformation.*, FreeRoamSurvey.*, DiceResult.* FROM (((PlayerInformation
Inner Join FreeRoamSurvey ON PlayerInformation.Id = FreeRoamSurvey.PlayerId )
INNER JOIN DiceResult ON PlayerInformation.Id = DiceResult.PlayerId)
INNER JOIN PlayerBrief ON PlayerInformation.Id = PlayerBrief.Id) WHERE PlayerBrief.SessionId = SESSION-ID-HERE 

-- Gives player details and round results for all tournament stages for a given session
SELECT PlayerInformation.*, RoundResult.* FROM ((PlayerInformation
INNER JOIN RoundResult ON PlayerInformation.Id = RoundResult.PlayerId )
INNER JOIN PlayerBrief ON PlayerInformation.Id = PlayerBrief.Id) WHERE PlayerBrief.SessionId = SESSION-ID-HERE AND RoundResult.Round >= 6