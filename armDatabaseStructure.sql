-- Table for result of one round of Mechanical Arm Mission
CREATE TABLE ArmRoundResult (
    Id int AUTO_INCREMENT PRIMARY KEY,
    Round int,
    -- Weight is a keyword
    Grams int,
    Cost int,
    SolverOne int,
    SolverTwo int,
    SolverThree int,
    SolverFour int,
    PlayerId varchar(255),
    FOREIGN KEY (PlayerId) REFERENCES PlayerBrief(Id),
    Architecture varchar(255),
    Score int
);

