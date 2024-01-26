#########################################################
# This function runs through all the architecture options
# Round (R), Whole hole (H), Drive-Approach-Putt (DAP), Long-Putt (LP) and Drive-Short(DS)
# v4 adds DAP to the update
# PNAS version removes strategy and always uses Rule 1
# This version changes the cost model and adds expert fraction
########################################################

source("SolverSim.R")

# Each function produces a matrix where model runs are columns and the rows take the following form:
# 1) the total round stroke count. 
# 2) the stroke count for the first subproblem
# 3) the stroke count for the second subproblem (if there is one)
# 4) the stroke count for the third subproblem (if there is one)
# 5) cost of work done (multiplier for experts, specialists and amateurs)
# 6) Scheduale for steady state 
# 7) Fraction Expert
#Then in repeting blocks of 25, the stroke history for each hole is recorded. The first entry is in row 6, then 2+buffer*(i-1)

#Sink <- 0.5
#ProCost <- 10
#SpecCost <- 9
#AmCost <- 1


############################
# This is the cost model
###########################
# Specialist costs too little right now

Cost <- function(Modules,Exp1,Exp2,Exp3,Size1,Size2,Size3,Work1,Work2,Work3,RuleD1,RuleD2){
  # Cost to coordinate
  if(RuleD1 == 2){
    cost_track1 <- Size1*TrackCost
  }else if(RuleD1 == 1){
    cost_track1 <- TrackCost
  }else{
    cost_track1 <- 0
  }
  if(RuleD2 == 2){
    cost_track2 <- Size2*TrackCost
  }else if(RuleD2 == 1){
    cost_track2 <- TrackCost
  }else{
    cost_track2 <- 0
  }
  # Cost to staff
  if(Exp1 == Pro){
    costM1 <- ProCost*Work1*Size1
  }else if(Exp1 == Am){
    costM1 <- AmCost + AmCost*Size1*0.1 #Pay for tournament, not work or size# change back to 0.1 for baseline
  }else if(Exp1 == Spec){
    costM1 <- SpecCost*Work1+((Size1-1)*SpecCost*0.1) # parantesis term for bidding cost
  }else{
    costM1 <- 0
  }
  if(Exp2 == Pro){
    costM2 <- ProCost*Size2*Work2
  }else if(Exp2 == Am){
    costM2 <- AmCost + AmCost*Size2*0.1 # change back to 0.1 for baseline
  }else if(Exp2 == Spec) {
    costM2 <- SpecCost*Work2+((Size2-1)*SpecCost*0.1) # parantesis term for bidding cost
  }else{
    costM2 <- 0
  }
  if(Exp3 == Pro){
    costM3 <- ProCost*Size3*Work1
  }else if(Exp3 == Am){
    costM3 <- AmCost + AmCost*Size3*0.1# change back to 0.1 for baseline
  }else if(Exp3 == Spec) {
    costM3 <- SpecCost*Work3+((Size3-1)*SpecCost*0.1)
  }else{
    costM3 <- 0
  }
  # Cost to decompose
  if(Modules == 1){
    cost_decomp <- 0
  }else{
    cost_decomp <- DecompCost
  }
#  cost_decomp <- (Modules-1)*DecompCost
  return(cost_decomp+costM1+costM2+costM3+cost_track1+cost_track2)
}


############################
# This runs the whole hole (H)
############################
#Figour out what to change

H_Arch <- function(HoleLength,Expertise,TournamentSize,Holes,runs){
  #Sink <- 0.1
  Result <- matrix(0,buffer*Holes+head,runs)
  #cat("results size =",size(Result),"\n")
  for (i in 1:runs){
    for (j in 1:Holes){
      start <- (j-1)*buffer+head-1
      #cat(":",start)
      end <- start+buffer-1
      #cat(end,"\n")
      Result[start:end,i] <- PlayWholeHole(HoleLength,Expertise,TournamentSize, Sink)
      Result[1,i] <- Result[1,i]+Result[(end-1),i]
      Result[2,i] <- Result[1,i]
      #Result[6,i] <- Result[6,i] + max(Result[2:4,i])
    }
    Result[5,i] <- Cost(1,Expertise,0,0,TournamentSize,0,0,Result[2,i]/Holes,Result[3,i]/Holes,Result[4,i]/Holes,0,0)
    Result[6,i] <- Result[1,i]/Holes
    if(Expertise == 1){
      Result[7,i] = 1
    } else {
      Result[7,i] = 0
    }
  }
  
  #PathTaken[TournamentSize*20+1] <- Numstrokes
  return(Result)
}

############################
# This runs the long + putt architecture. 
###########################
# Rule 1 is practica, Rule 2 is optimal, Rule 3 is decoupled

LP_Arch <- function(HoleLength, Expertise_L, Expertise_P, TournamentSize_L, TournamentSize_P,Rule,Holes,runs){
  Result <- matrix(0,buffer*Holes+head,runs)
  cat(Result)
  #NumStrokes <- 0L
  for (i in 1:runs){
    for (j in 1:Holes){
      Long <- rep(0,(sizeD+sizeF))
      Temp <- rep(0,buffer)
      if(Rule == 1){
        Long <- PlayLong(HoleLength,Expertise_L,TournamentSize_L,1)
        LongStrokes <- Long[sizeD+sizeF-1]
        BallNow <- Long[sizeD+sizeF]
      } else if(Rule == 2){
        Long <- PlayLong(HoleLength,Expertise_L,TournamentSize_L,2)
        LongStrokes <- Long[sizeD+sizeF-1]
        BallNow <- Long[sizeD+sizeF]
      } else {
        NewTarget <- HoleLength - GreenTransition
        # Find my issue!!!!!!!
        Temp <- PlayWholeHole(NewTarget,Expertise_L,TournamentSize_L,zone)
        #cat("Temp is:",Temp,"\n")
        LongStrokes <- Temp[buffer-1]
        #cat("strokes is:",LongStrokes,"\n")
        ######## does this need to be Temp[buffer]
        BallNow <- Temp[buffer]+GreenTransition
        #cat("ball now is:",BallNow,"\n")
        Long <- Temp + GreenTransition
        #cat("long is:",Long,"\n")
      }
      #cat("long is:",Long,"\n")
      start <- (j-1)*buffer+head+1
      end <- start+LongStrokes
      #cat("when j is",j,"start is",start,"and end is",end,"\n")
      #cat("longstrokes is:",LongStrokes)
      Result[start:end,i] <- Long[1:(LongStrokes+1)]
      Putt <- rep(0,sizeP)
      Putt <- PlayPutt(BallNow,Expertise_P,TournamentSize_P,Sink)
      #cat("putt is:",Putt,"\n")
      PuttStrokes <- Putt[sizeP-1]
      start <- end
      end <- start+PuttStrokes
      Result[start:end,i] <- Putt[1:(PuttStrokes+1)] # problem is here
      Result[((j-1)*(buffer)+(buffer+head-1)),i] <- LongStrokes+PuttStrokes
      Result[((j-1)*(buffer)+(buffer+head)),i] <- Putt[sizeP]
      Result[1,i] <- Result[1,i]+ Result[((j-1)*(buffer)+(buffer+head-1)),i]
      if(Rule == 3){
        Result[6,i] <- Result[6,i] + max(c(LongStrokes,PuttStrokes))# in steady state
        Result[7,i] <- Result[6,i]
      } else {
        Result[6,i] <- Result[6,i] + max(c(LongStrokes,PuttStrokes))# in steady state
        Result[7,i] <- Result[1,i]
      }
      Result[2,i] <- Result[2,i] + LongStrokes
      Result[3,i] <- Result[3,i] + PuttStrokes
      # Calculating fraction of work done by experts
      Fraction <- 0
      if (Expertise_L == 1){
        Fraction <- LongStrokes
      }
      if (Expertise_P ==1){
        Fraction <- Fraction + PuttStrokes
      }
      Result[7,i] <- Fraction/(LongStrokes + PuttStrokes)
      #cat("result is:",Result,"\n")
    }
    Result[5,i] <- Cost(2,Expertise_L,Expertise_P,0,TournamentSize_L,TournamentSize_P,0,Result[2,i]/Holes,Result[3,i]/Holes,Result[4,i]/Holes,Rule,0)
    Result[6,i] <- Result[6,i]/Holes
    #Result[7,i] <- Result[7,i]/Holes
  }
  return(Result)
}

###########################
# This is the drive-fairway-putt architecture (DAP)
###########################

### Adopt fixe when use non PNAS - DAP need to swithch fairway to play from ballnow.

DAP_Arch <- function(HoleLength,Expertise_D,Expertise_F,Expertise_P,TournamentSize_D,TournamentSize_F,TournamentSize_P,RuleDF,RuleFP,Holes,runs){
  Result <- matrix(0,buffer*Holes+head,runs)
  for (i in 1:runs){
    for (j in 1:Holes){
      # the D subproblem
      drive <- rep(0,sizeD)
      Temp <- rep(0,buffer)
      #cat("here 1")
      if(RuleDF == 1){
        #cat("here 1a")
        drive <- PlayDrive(HoleLength,Expertise_D,TournamentSize_D,1,0)
        DriveStrokes <- drive[sizeD-1]
        BallNow <- drive[sizeD]
      } else if (RuleDF == 2){
        #cat("here 1b")
        drive <- PlayDrive(HoleLength,Expertise_D,TournamentSize_D,2,0)
        DriveStrokes <- drive[sizeD-1]
        BallNow <- drive[sizeD]
      } else {
        #cat("here 1c")
        NewTarget <- HoleLength - FairwayTransition
        Temp <- PlayWholeHole(NewTarget,Expertise_D,TournamentSize_D,zone)
        #cat("long is:",Temp,"\n")
        DriveStrokes <- Temp[buffer-1]
        #cat("strokes is:",LongStrokes,"\n")
        BallNow <- Temp[buffer]+FairwayTransition
        #cat("ball now is:",BallNow,"\n")
        drive <- Temp + FairwayTransition
      }
      start <- (j-1)*buffer+8
      end <- start+DriveStrokes
      Result[start:end,i] <- drive[1:(DriveStrokes+1)]
      ### Approach
      Approach <- rep(0,(sizeF))
      Temp <- rep(0,buffer)
      if(RuleFP == 1){
        Approach <- PlayFairway(BallNow,Expertise_F,TournamentSize_F,1,0) # I turned the strategy off here after speaking with Zoe
        ApproachStrokes <- Approach[sizeF-1]
        BallNow <- Approach[sizeF]
      } else if(RuleFP == 2){
        Approach <- PlayFairway(BallNow,Expertise_F,TournamentSize_F,2,0) # I turned the strategy off here after speaking with Zoe
        ApproachStrokes <- Approach[sizeF-1]
        BallNow <- Approach[sizeF]
      } else {
        NewTarget <- BallNow - GreenTransition
        # Find my issue!!!!!!!
        Temp <- PlayWholeHole(NewTarget,Expertise_F,TournamentSize_F,zone)
        #cat("Temp is:",Temp,"\n")
        ApproachStrokes <- Temp[buffer-1]
        #cat("strokes is:",LongStrokes,"\n")
        ######## does this need to be Temp[buffer]
        BallNow <- Temp[buffer]+GreenTransition
        #cat("ball now is:",BallNow,"\n")
        Approach <- Temp + GreenTransition
        #cat("long is:",Long,"\n")
      }
      start <- end+1 # delete +1 if it doesn't solve anything.
      end <- start+ApproachStrokes
      Result[start:end,i] <- Approach[1:(ApproachStrokes+1)]
      ## This is where Putting stage begins
      Putt <- rep(0,sizeP)
      Putt <- PlayPutt(BallNow,Expertise_P,TournamentSize_P,Sink)
      #cat("putt is:",Putt,"\n")
      PuttStrokes <- Putt[sizeP-1]
      start <- end
      end <- start+PuttStrokes
      Result[start:end,i] <- Putt[1:(PuttStrokes+1)]
      Result[((j-1)*(buffer)+(buffer+head-1)),i] <- DriveStrokes+ApproachStrokes+PuttStrokes
      #cat(((j-1)*(buffer+4)+(buffer+4)),"=", DriveStrokes, FairwayStrokes,PuttStrokes)
      Result[((j-1)*(buffer)+(buffer+head)),i] <- Putt[sizeP]
      #cat(Putt[sizeP])
      #cat("drive is:", drive,"\n","approach is:",approach,"\n","Putt is:",Putt,"\n","Result is:",Result,"\n")
      Result[1,i] <- Result[1,i]+Result[((j-1)*(buffer)+(buffer+head-1)),i]
      Result[2,i] <- Result[2,i] + DriveStrokes
      #cat("Result is:",Result,"\n")
      Result[3,i] <- Result[3,i] + ApproachStrokes
      Result[4,i] <- Result[4,i] + PuttStrokes
      if(RuleDF == 3&RuleFP==3){
        Result[6,i] <- Result[6,i] + max(c(DriveStrokes,ApproachStrokes,PuttStrokes))# in steady state
        #Result[7,i] <- Result[6,i]
      } else if (RuleDF == 3){
        Result[6,i] <- Result[6,i] + max(c(DriveStrokes,ApproachStrokes,PuttStrokes))# in steady state
        #Result[7,i] <- Result[6,i] + max(c(DriveStrokes,ApproachStrokes))+PuttStrokes
      } else if (RuleFP == 3){
        Result[6,i] <- Result[6,i] + max(c(DriveStrokes,ApproachStrokes,PuttStrokes))# in steady state
        #Result[7,i] <- Result[6,i] + max(c(PuttStrokes,ApproachStrokes))+DriveStrokes
      } else {
        Result[6,i] <- Result[6,i] + max(c(DriveStrokes,ApproachStrokes,PuttStrokes))# in steady state
        #Result[7,i] <- Result[1,i]
      }
      Fraction <- 0
      if (Expertise_D == 1){
        Fraction <- DriveStrokes
      }
      if (Expertise_F ==1){
        Fraction <- Fraction + ApproachStrokes
      }
      if (Expertise_P ==1){
        Fraction <- Fraction + PuttStrokes
      }
      Result[7,i] <- Fraction/(DriveStrokes + ApproachStrokes + PuttStrokes)
    }
    Result[5,i] <- Cost(3,Expertise_D,Expertise_F,Expertise_P,TournamentSize_D,TournamentSize_F,TournamentSize_P,Result[2,i]/Holes,Result[3,i]/Holes,Result[4,i]/Holes,RuleDF,RuleFP)
    Result[6,i] <- Result[6,i]/Holes
    #Result[7,i] <- Result[7,i]/Holes
  }
  return(Result)
}


#############################
# The runs Drive-Short (DS)
#############################

DS_Arch <- function(HoleLength,Expertise_D,Expertise_S,TournamentSize_D,TournamentSize_S,Rule,Holes,runs){
  Result <- matrix(0,buffer*Holes+7,runs)
  for (i in 1:runs){
    for (j in 1:Holes){
      drive <- rep(0,sizeD)
      Temp <- rep(0,buffer)
      #cat("here 1")
      if(Rule == 1){
        #cat("here 1a")
        drive <- PlayDrive(HoleLength,Expertise_D,TournamentSize_D,1,0)
        DriveStrokes <- drive[sizeD-1]
        BallNow <- drive[sizeD]
      } else if (Rule == 2){
        #cat("here 1b")
        drive <- PlayDrive(HoleLength,Expertise_D,TournamentSize_D,2,0)
        DriveStrokes <- drive[sizeD-1]
        BallNow <- drive[sizeD]
      } else {
        #cat("here 1c")
        NewTarget <- HoleLength - FairwayTransition
        Temp <- PlayWholeHole(NewTarget,Expertise_D,TournamentSize_D,zone)
        #cat("long is:",Temp,"\n")
        DriveStrokes <- Temp[buffer-1]
        #cat("strokes is:",LongStrokes,"\n")
        BallNow <- Temp[buffer]+FairwayTransition
        #cat("ball now is:",BallNow,"\n")
        drive <- Temp + FairwayTransition
      }
      #cat(drive)
      #cat("here 2")
      start <- (j-1)*buffer+8
      end <- start+DriveStrokes
      #cat("when j is",j,"start is",start,"DriveStrokes is:", DriveStrokes,"and end is",end,"\n")
      Result[start:end,i] <- drive[1:(DriveStrokes+1)]
      short <- rep(0,(sizeF+sizeP))
      short <- PlayShort(BallNow,Expertise_S,TournamentSize_S,Sink)
      ShortStrokes <- short[sizeF+sizeP-1] 
      BallNow <- short[sizeF+sizeP]
      start <- end
      end <- start+ ShortStrokes
      #cat("here 1:", ShortStrokes)
      Result[start:end,i] <- short[1:(ShortStrokes+1)]
      #cat("here 2")
      Result[((j-1)*buffer+buffer+6),i] <- DriveStrokes+ShortStrokes
      Result[((j-1)*buffer+buffer+7),i] <- BallNow
      Result[1,i] <- Result[1,i]+Result[((j-1)*buffer+buffer+6),i]
      Result[2,i] <- Result[2,i] + DriveStrokes
      Result[3,i] <- Result[3,i] + ShortStrokes
      if(Rule == 3){
        Result[6,i] <- Result[6,i] + max(c(DriveStrokes,ShortStrokes))# in steady state
        #Result[7,i] <- Result[6,i] #for a given hole
      } else {
        Result[6,i] <- Result[6,i] + max(c(DriveStrokes,ShortStrokes))# in steady state
        #Result[7,i] <- Result[1,i]
      }
      Fraction <- 0
      if (Expertise_D == 1){
        Fraction <- DriveStrokes
      }
      if (Expertise_S ==1){
        Fraction <- Fraction + ShortStrokes
      }
      Result[7,i] <- Fraction/(DriveStrokes + ShortStrokes)
      #cat("result is:",Result,"\n")
    }
    Result[5,i] <- Cost(2,Expertise_D,Expertise_S,0,TournamentSize_D,TournamentSize_S,0,Result[2,i]/Holes,Result[3,i]/Holes,Result[4,i]/Holes,Rule,0)
    Result[6,i] <- Result[6,i]/Holes
    #Result[7,i] <- Result[7,i]/Holes
  }
  return(Result)
}

#############################
# This runs the round (R)
#############################
# Fix this

R_Arch <- function(HoleLength,Expertise,TournamentSize,Holes,runs){
  Result <- matrix(1000000000000,buffer*Holes+head,runs)
  #cat("results size =",size(Result),"\n")
  for (i in 1:runs){
    for (k in 1:TournamentSize){
      ResultTemp <- rep(0,buffer*Holes+head)
      for (j in 1:Holes){
        start <- (j-1)*buffer+head+1
        #cat(":",start)
        end <- start+buffer-1
        #cat(end,"\n")
        ResultTemp[start:end] <- PlayWholeHole(HoleLength,Expertise,1,Sink)
        ResultTemp[1] <- ResultTemp[1]+ResultTemp[(end-1)]
        ResultTemp[2] <- ResultTemp[1]
        #Result[6,i] <- Result[6,i] + max(Result[2:4,i])
      }
      if(ResultTemp[1]<Result[1,i]){
        Result[,i] <- ResultTemp
      }
    }
    Result[5,i] <- Cost(1,Expertise,0,0,TournamentSize,0,0,Result[2,i]/Holes,Result[3,i]/Holes,Result[4,i]/Holes,0,0)
    Result[6,i] <- Result[1,i]/Holes
    Result[7,i] <- Result[6,i]
  }
  
  #PathTaken[TournamentSize*20+1] <- Numstrokes
  return(Result)
}
