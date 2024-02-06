-- SQL database structure and commands for instantiating database, querying database, etc. 

-- Session Table:
CREATE TABLE session (
    JoinCode int PRIMARY KEY,
    Round int NULL,
    StartDate varchar(255),
    EndDate varchar(255),
);

-- If there is only a value for SolverOne and not SolverTwo and SolverThree and if the round is 1 or 2 
-- then h_arch was used.
-- If there is only values for SolverOne and SolverTwo and not SolverThree and if the round is 3 then
-- lp_arch was used.
-- If there are values for SolverOne, SolverTwo, and SolverThree and if the round is 4 then dap_arch was used.
-- Solver are ints where: 1 -> Professional, 2 -> Amatuer, 3 -> Specialist
-- Round Result Table:
CREATE TABLE RoundResult (
    Id int IDENTITY(1,1) PRIMARY KEY,
    Round int,
    Shots int,
    Cost int,
    SolverOne int,
    SolverTwo int,
    SolverThree int,
    PlayerId varchar(255) FOREIGN KEY REFERENCES PlayerBrief(Id),
);

-- Player Brief Table:
CREATE TABLE PlayerBrief (
    Id varchar(255) PRIMARY KEY,
    Name varchar(255),
    Color varchar(255),
    SessionId int FOREIGN KEY REFERENCES session(JoinCode),
)

-- Player Information Table:
CREATE TABLE PlayerInformation (
    Id varchar(255) PRIMARY KEY,
    Name varchar(255),
    ParticipationReason varchar(255),
    Gender varchar(255),
    Age int,
    Country varchar(255),
    Hobbies varchar(255),
    IsCollegeStudent bit,
    University varchar(255),
    DegreeProgram varchar(255),
    YearsInProgram int,
    HighSchoolEducation varchar(255),
    AssociatesEducation varchar(255),
    BachelorsEducation varchar(255),
    MastersEducation varchar(255),
    ProfessionalEducation varchar(255),
    DoctorateEducation varchar(255),
    OtherEducation varchar(255),
    OtherEducationName varchar(255),
    AerospaceEngineeringSpecialization varchar(255),
    DesignSpecialization varchar(255),
    ElectricalEngineeringSpecialization varchar(255),
    IndustrialEngineeringSpecialization varchar(255),
    ManufacturingSpecialization varchar(255),
    MaterialScienceSpecialization varchar(255),
    MechanicalEngineeringSpecialization varchar(255),
    SoftwareSpecialization varchar(255),
    SystemsEngineeringSpecialization varchar(255),
    OtherSpecialization varchar(255),
    OtherSpecializationName varchar(255),
    SystemsEngineeringExpertise int,
    StatementOfWorkExpertise int,
)