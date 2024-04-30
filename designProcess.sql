-- table for new user info - make email a foreign key
CREATE TABLE User (
    Email varchar(255) PRIMARY KEY,
    Password varchar(255),
    Gender varchar(255),
    Age int,
    Ethnicity varchar(255), -- Ethnicity (taken from Stanford: https://idealdeisurvey.stanford.edu/frequently-asked-questions/survey-definitions)
    Employer varchar(255),
    Team varchar(255),
    Title varchar(255),

    -- each education field will now be prefaced with "yes" or "current" to tell if person is actively a student or not.
    -- removed associates and proffesional educations
    BachelorsEducation varchar(255),
    MastersEducation varchar(255), 
    DoctorateEducation varchar(255),
    OtherEducation varchar(255),
    OtherEducationName varchar(255),

    -- specialization questions:
    AerodynamicsSpecialization int,
    ComputerScienceSpecialization int,
    ElectricalEngineeringSpecialization int,
    ElectromagneticsSpecialization int,
    EnvironmentalTestingSpecialization int,
    LogisticsSpecialization int,
    ManufacturingSpecialization int,
    MechanicalDesignSpecialization int,
    OperationsResearchSpecialization int,
    ProjectManagementSpecialization int,
    SystemsEngineeringSpecialization int,
    StructuralAnalysisSpecialization int,
    ThreatAnalysisSpecialization int,
    OtherSpecializationName varchar(255),
    OtherSpecialization int,

    -- Navy agency questions:
    ShipyardAgency int,
    NavseaAgency int,
    NswcDahlgrenAgency int,
    NswcCarderockAgency int,
    OpnavAgency int,
    PentagonAgency int,
    OtherNswcAgencyName varchar(255),
    OtherAgency int,

    -- 7 point experience questions:
    RiskAnalysisExperience int,
    SupplierExperience int,

    -- 7 point familiarity questions:
    ProjectContextFamiliarity int,
    NavyPlatformFamiliarity int,
    DesignChangeCharacteristicsFamiliarity int
)

-- table for measurement period (connects records)
CREATE TABLE topcu.MeasurementPeriod (
    Id int AUTO_INCREMENT, 
    PRIMARY KEY (Id),
    Email varchar(255),
    StartDate varchar(255),
    EndDate varchar(255),
    Entered varchar(255),
    FOREIGN KEY (Email) REFERENCES User(Email)
)


-- table for one activity record
CREATE TABLE ActivityRecord (
    Id int AUTO_INCREMENT,
    PRIMARY KEY (Id),
    MeasurementPeriod int, 
    FOREIGN KEY (MeasurementPeriod) REFERENCES MeasurementPeriod(Id),
    Type varchar(255),
    Duration int,
    Question1 varchar(255),
    Question2 varchar(255),
    Question3 varchar(255),
    pointScale int
)