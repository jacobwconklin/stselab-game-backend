##############################
# Source this file to run golf. 
# It is built on the code from GolfTournament_v3.0.R
# It spits out a vectors of the path to solve the run and also the strokes per run
# Use it for either stroke analysis or path analysis.
# PNAS version removes strategy
################################

##################################################################
# For this version of golf there are exactly four kinds of strokes: hit off the tee (Drive), hit as far as you can from the fairway (LFairway)
# aim for green (or sweetspot) (AFairway) and try to sink it (putt)

# Each of the functions just do the random draw from the relevant distribution
# I'm building in a little strategy. My brother said he pulls up to 100 yards because he can aim well with an iron from that distance.

# I had originally set these up so that you could run them a bunch of times here,
# but n should always be 1. The tournament happens at a higher level.
###################################################################

####################################
# Here I'm defining the types of solvers I can draw from for the tournaments.
#Eventually this will be read in from a csv file. I'm imaging many rows of solver types.
#Currently I am just having two types: Pro's who are good at everything and have strategies. Novices who are bad at everything and have
#no strategy. Specialists who are great at driving off the tee and otherwise behave like novices.

Solver <- data.frame(     
  Type = c("Pro", "Novice", "Specialist"),
  Drive_mean = c(250L, 150L, 450L),
  Drive_sd = c(15L, 30L, 30L),
  Drive_Fairway_handoff = c(FairwayTransition,FairwayTransition,FairwayTransition),
  LFairway_mean = c(200L,100L,100L),  
  LFairway_sd = c(10L,20L,20L),
  AFairway_sd_factor = c(0.05,0.2,0.2), #accuracy is a function of distance
  AFairway_sd_sweetspot = c(0.03,0.05,0.05), #accuracy is a function of distance
  Fairway_sweetspot = c(75L,0L,0L),
  Fairway_Putt_handoff = c(GreenTransition,GreenTransition,GreenTransition),
  Putt_prob = c(0.80,0.20,0.20),
  Goodputt_sd_factor = c(0.01,0.05,0.05),
  Badputt_min = c(0,0,0),
  Badputt_max = c(10,15,15)
)

############### Need to change how strategy is implemented, so that there's an advantage not a disadvantage
# Long fairway is like driving just less effective.
############### Need to change how strategy is implemented, so that there's an advantage not a disadvantage
# Long fairway is like driving just less effective.
LFairway <- function (target, Expertise, strategy, n=1){
  #strategy <- 0
  if(Expertise== 2 | Expertise == 3){
    strategy <- 0} ## I placed it here because this function is cal
  RemainingDistance <- min(abs(target - rnorm(n,Solver[Expertise,c('LFairway_mean')],Solver[Expertise,c('LFairway_sd')])))
  #  if (RemainingDistance>0.001 && RemainingDistance<Offset){
  #    RemainingDistance<-1
  #  }
  #  if (RemainingDistance<=Sink){RemainingDistance <- Sink+0.1} ### 
  return(RemainingDistance)
}

# Aiming fairway aims near the pin. If Experts are in their sweetspot, they're really accurate. Novices don't have a sweet spot.
AFairway <- function(target, Expertise, n=1, strategy){
  #strategy <- 0
  if(Expertise== 2 | Expertise == 3){
    strategy <- 0} ## I placed it here because this function is cal
  if (strategy ==1 & Expertise == 1){ #If it's a subproblem with strategy and you're an expert you can aim
    RemainingDistance <- min(abs(target - rnorm(n,(target-0.5*Offset),target*Solver[Expertise,c('AFairway_sd_sweetspot')])))      
  } 
  
  if ((strategy == 0 && Expertise == 1) || Expertise == 2 || Expertise == 3) {
    RemainingDistance <- min(abs(target - rnorm(n,(target-Offset),target*Solver[Expertise,c('AFairway_sd_factor')])))
  }
  #      if (RemainingDistance>0.001 && RemainingDistance<Offset){
  #        RemainingDistance<-1
  #      }
  #  if (RemainingDistance<=Sink){RemainingDistance <- Sink+0.1}
  return(RemainingDistance)
}

# Edited from earlier: add strategy to driving. Only drive if you control the next one.

Drive <- function (target,Expertise, strategy, n=1) {
  #strategy <- 0 # 9/14/20 bi boyle dene olmazsa buraya   if(Expertise==1) fln tarzi bir gate koy
  if(Expertise== 2 | Expertise == 3){
    strategy <- 0} ## I placed it here because this function is cal ## I placed it here because this function is called by all architectures and this was the only way to decouple the strategy.
  if(Solver[Expertise,c('Drive_mean')]>target){
    RemainingDistance <- LFairway(target,Expertise,strategy,1)
  }else{
    RemainingDistance <- min(abs(target - rnorm(n,Solver[Expertise,c('Drive_mean')],Solver[Expertise,c('Drive_sd')])))  
  }
  return(RemainingDistance)
}

# Drive <- function (target,Expertise, strategy, n=1) {
#   #strategy <- 0 # 9/14/20 bi boyle dene olmazsa buraya   if(Expertise==1) fln tarzi bir gate koy
#   if(Solver[Expertise,c('Drive_mean')]>target){
#     RemainingDistance <- LFairway(target,Expertise,strategy,1)
#   }else{
#     RemainingDistance <- min(abs(target - rnorm(n,Solver[Expertise,c('Drive_mean')],Solver[Expertise,c('Drive_sd')])))  
#   }
#   return(RemainingDistance)
# }

#This is trying to sink (I'm not currently implementing a putting strategy for experts)
Putt <- function (target, Expertise, n=1) {
  #I want it to randomly flip between good shots and bad shots, so I'm a random number from 0 to 1 is bigger than the flip condition..
  if (runif(1,0,1) < Solver[Expertise,c('Putt_prob')]) {
    RemainingDistance <- min(abs(target - rnorm(n,target,target*Solver[Expertise,c('Goodputt_sd_factor')])))
  } else {
    RemainingDistance <- min(abs(target - runif(n,Solver[Expertise,c('Badputt_min')],Solver[Expertise,c('Badputt_max')])))
  }
  return(RemainingDistance)
}

############################################################################################
# Design rules are also a base function. I can use different decision rules to do the handoff
# I did this differently when I was running the path function, so I need to come back and check
# if it still belongs here.
#############################################################################################
#!!!!!! Need to update this with the vector version

#PickBest <- function(distance,strokes,rule){
#  if (rule == 1) { # pick the closest to the hole
#    z <- order(distance)
#    best <- z[1]
#  } else { # of the ones with the fewest strokes, pick the one that's closest to the hole.
#    dist_normalized <- distance/max(distance)
#    # This is because distances are bigger than stroke numbers and I mostly want to sort on strokes
#    z <- order(strokes+dist_normalized)
#    # I was having trouble trying to access order directly, so I'm assigning it to a made up vector
#    best <- z[1]
#  }
#  # There's probably a better way to pass to parameters...
#  result <- c(distance[best],strokes[best])
#  return(result)
#}


##########################
# Now I'm creating functions to run subproblems within golf. Eventually  I will want to be able to call every version of subproblem to make a whole hole.

############################################
# This function putts until you sink
# This has been revised since 2.4 to also track the solving PathTaken.
# It now returns a vector of the path taken, with the last element being the number of strokes. 
# It only returns the best path for the N tries.

PlayPutt <- function(BallNow, Expertise, N,size){
  Start <- BallNow
  PathTaken <- rep(100,sizeP) # Come back!!! This needs a variable name.
  for (i in 1:N){
    PathTakenAlt <- rep(0.1,sizeP)
    NumStrokes <- 0L
#   BallNow <- Start ## We think This fixes the model by forcing everyone to take at least one put 10/5 
    BallNow <- Putt(Start,Expertise) 
    NumStrokes <- 1L
    while (abs(BallNow) > size){
      BallNow <-  Putt(BallNow,Expertise)
      NumStrokes = NumStrokes + 1
      #cat ("when i is",i, "NumStrokes is", NumStrokes, "and j is", j, "\n")
      if(NumStrokes > 14){ # Mercy rule
        BallNow <- 0
        NumStrokes = NumStrokes +1
      }
      PathTakenAlt[NumStrokes] <- BallNow #continuing to write the PathTaken to this vector
    }
    PathTakenAlt[sizeP-1] <- NumStrokes
    PathTakenAlt[sizeP] <- BallNow
    #cat("For i = ",i,"PathTaken is", PathTaken, "and PathTakenAlt is", PathTakenAlt)
    
    # Best is defined as fewest strokes to sink
    if(PathTakenAlt[sizeP-1]<PathTaken[sizeP-1]){
      PathTaken <- PathTakenAlt
    }
  }
  return(PathTaken)
}

####################################
# This is the fairway function. It starts with a handoff from the drive and takes it until it first crosses the green transition     #
####################################
PlayFairway <- function(BallNow,Expertise,N,rule,strategy){
  #strategy <- 0 # removing strategy
  Start <- BallNow
  PathTaken <- rep(1000,sizeF)
  for (i in 1:N){
    PathTakenAlt <- rep(0.1,sizeF)
    NumStrokes <- 0L
    BallNow <- Start
    while (BallNow > Solver[Expertise,c('Fairway_Putt_handoff')]){
      if (BallNow > (Solver[Expertise,c('LFairway_mean')])){
        BallNow <- LFairway(BallNow, Expertise,strategy,1)
      } else {
        BallNow <- AFairway(BallNow,Expertise,1,strategy)
      }
      NumStrokes = NumStrokes + 1
      PathTakenAlt[NumStrokes] <- BallNow #continuing to write the PathTaken to this vector
    }
    PathTakenAlt[sizeF-1] <- NumStrokes
    PathTakenAlt[sizeF] <- BallNow
    #cat("For i = ",i,"PathTaken is", PathTaken, "and PathTakenAlt is", PathTakenAlt)
    # For rule 1, best is defined as the closest ball (ignores strokes)
    if(PathTakenAlt[sizeF]<PathTaken[sizeF] & rule==1){
      PathTaken <- PathTakenAlt
    }
    # For rule 2, best is defined as the one with the fewest strokes, that is closest to the hole.
    if(PathTakenAlt[sizeF-1]<PathTaken[sizeF-1] & rule==2){
      PathTaken <- PathTakenAlt
    } 
    if((PathTakenAlt[sizeF-1]==PathTaken[sizeF-1])&(PathTakenAlt[sizeF]<PathTaken[sizeF]) & rule == 2){
      PathTaken <- PathTakenAlt
    }
    #cat( "So we keep", PathTaken,"\n")
  }
  return(PathTaken)
}
#####################################
# This function drives until you cross the fairway transition #
#####################################

PlayDrive <- function(HoleDist,Expertise,N,rule,strategy){
  #strategy <- 0 #removing strategy
  Start <- HoleDist
  PathTaken <- rep(1000,sizeD)
  for (i in 1:N){
    PathTakenAlt <- rep(0.1,sizeD)
    NumStrokes <- 1
    BallNow <- Start
    PathTakenAlt[NumStrokes] <- BallNow
    BallNow <- Drive(HoleDist,Expertise,strategy,1)
    PathTakenAlt[NumStrokes+1] <- BallNow
    PathTakenAlt[sizeD-1] <- NumStrokes
    PathTakenAlt[sizeD] <- BallNow
    #cat("For i = ",i,"PathTaken is", PathTaken, "and PathTakenAlt is", PathTakenAlt)
    if(PathTakenAlt[sizeD]<PathTaken[sizeD] & rule==1){
      #cat(PathTakenAlt[sizeD],"vs.",PathTaken[sizeD])
      PathTaken <- PathTakenAlt
    }
    # For rule 2, best is defined as the one with the fewest strokes, that is closest to the hole.
    if(PathTakenAlt[sizeD-1]<PathTaken[sizeD-1] & rule==2){
      PathTaken <- PathTakenAlt
    } 
    if((PathTakenAlt[sizeD-1]==PathTaken[sizeD-1])&(PathTakenAlt[sizeD]<PathTaken[sizeD]) & rule == 2){
      PathTaken <- PathTakenAlt
    }
    #cat( "So we keep", PathTaken,"\n")
  }
  return(PathTaken)
}


#####################################
# This function starts from the tee and plays until the green transition
#####################################

PlayLong <- function(BallNow,Expertise,N,rule){
  # removed strategy when it's executed - TT. I tried to put the strategy back, lets see if it works. 
  PathTaken <- rep(100,sizeD+sizeF) #allowing max strokes with an extra element for count 
  for (i in 1:N){
    PathTakenTemp <- rep(0.1,sizeD+sizeF)
    #PathTakenTemp[1] <- BallNow
    drive <- rep(0,sizeD)
    drive <- PlayDrive(BallNow,Expertise,1,2,1)
    #cat("drive is:",drive,"\n")
    NumStrokes <- drive[sizeD-1]
    CurrentBall <- drive[sizeD]
    PathTakenTemp[1:(NumStrokes+1)] <- drive[1:(NumStrokes+1)]
    #fairway
    fairway <- rep(0,sizeF)
    fairway <- PlayFairway(CurrentBall,Expertise,1,1,1) #no knowledge of what putter wants.
    #cat("fairway is:",fairway,"\n")
    NumStrokesFairway <- fairway[sizeF-1]
    StrokesAfterFairway <- NumStrokesFairway+NumStrokes
    CurrentBall <- fairway[sizeF]
    PathTakenTemp[(NumStrokes+2):(StrokesAfterFairway+1)] <- fairway[1:NumStrokesFairway]
    PathTakenTemp[sizeD+sizeF-1] <- StrokesAfterFairway
    PathTakenTemp[sizeD+sizeF] <- fairway[sizeF]
    if(PathTakenTemp[sizeD+sizeF]<PathTaken[sizeD+sizeF] & rule == 1){
      PathTaken <- PathTakenTemp
    }
    # For rule 2, best is defined as the one with the fewest strokes, that is closest to the hole.
    if(PathTakenTemp[sizeD+sizeF-1]<PathTaken[sizeD+sizeF-1] & rule==2){
      PathTaken <- PathTakenTemp
    } 
    if((PathTakenTemp[sizeD+sizeF-1]==PathTaken[sizeD+sizeF-1])&(PathTakenTemp[sizeD+sizeF]<PathTaken[sizeD+sizeF]) & rule == 2){
      PathTaken <- PathTakenTemp
    }
    #cat("PathTaken is:",PathTaken,"\n")
  }
  return(PathTaken)
}

#####################################
# This function starts from the fairway transition and plays until you sink
#####################################

PlayShort <- function(BallNow,Expertise,N,size){
  PathTaken <- rep(100000000,sizeF+sizeP) #allowing max strokes with an extra element for count 
  #strokes <- rep(0,N)
  for (i in 1:N){
    PathTakenTemp <- rep(0.1,sizeF+sizeP)
    PathTakenTemp[1] <- BallNow
    #Fairway
    fairway <- rep(0,sizeF)
    fairway <- PlayFairway(BallNow,Expertise,1,2,0) #strategy because you can set up your <- too. ## the rule was =2 here so I fixed that
    #cat("fairway is:",fairway,"\n")
    StrokesFairway <- fairway[sizeF-1]
    CurrentBall <- fairway[sizeF]
    PathTakenTemp[2:(StrokesFairway+1)] <- fairway[1:StrokesFairway]
    #Putt
    putt <- rep(0,sizeP)
    putt <- PlayPutt(CurrentBall,Expertise,1,size)
    #cat("putt is:",putt,"\n")
    NumStrokesPutt <- putt[sizeP-1]
    StrokesAfterPutt <- StrokesFairway + NumStrokesPutt
    PathTakenTemp[(StrokesFairway+2):(StrokesAfterPutt+1)] <- putt[1:NumStrokesPutt]
    PathTakenTemp[sizeF+sizeP-1] <- StrokesAfterPutt
    PathTakenTemp[sizeF+sizeP] <- putt[sizeP]
    
    #No need for rules because we're playing to the hole.
    if(PathTakenTemp[sizeF+sizeP-1]<PathTaken[sizeF+sizeP-1]){
      PathTaken <- PathTakenTemp
    }
    #cat("PathTaken is:",PathTaken,"\n")
  }
  # Returns a vector where the first stroke is the starting position.
  return(PathTaken)
}

#####################################
# This function starts from the tee and plays until you sink
#####################################
#!!!!!!Update to return a vector that's the best of N plays the whole hole

PlayWholeHole <- function(BallNow,Expertise,N,size){
  PathTaken <- rep(1000000000,buffer) #allowing max strokes with an extra element for count 
  for (i in 1:N){
    PathTakenTemp <- rep(0,buffer)
    #PathTakenTemp[1] <- BallNow
    #drive
    if(BallNow==HoleLength){
                        #### This is what we added to prevent DS guys from driving one more time (Which we think was granting Ams an advantage)
    drive <- rep(0,sizeD)
    drive <- PlayDrive(BallNow,Expertise,1,2,1) #rule=2 because this is whole hole; strategy could be removed
    #cat("drive is:",drive,"\n")
    NumStrokes <- drive[sizeD-1]
    CurrentBall <- drive[sizeD]
    PathTakenTemp[1:(NumStrokes+1)] <- drive[1:(NumStrokes+1)]
    } else{CurrentBall <-BallNow} ## this should  
    #fairway
    fairway <- rep(0,sizeF)
    fairway <- PlayFairway(CurrentBall,Expertise,1,2,1)
    #cat("fairway is:",fairway,"\n")
    NumStrokesFairway <- fairway[sizeF-1]
    StrokesAfterFairway <- NumStrokesFairway+NumStrokes
    CurrentBall <- fairway[sizeF]
    PathTakenTemp[(NumStrokes+2):(StrokesAfterFairway+1)] <- fairway[1:NumStrokesFairway]
    #putt
    putt <- rep(0,sizeP)
    putt <- PlayPutt(CurrentBall,Expertise,1,size)
    #cat("putt is:",putt,"\n")
    #cat("here's the putt:",putt,"\n")
    NumStrokesPutt <- putt[sizeP-1]
    if (NumStrokesPutt >0){
      StrokesAfterPutt <- StrokesAfterFairway + NumStrokesPutt
      PathTakenTemp[(StrokesAfterFairway+2):(StrokesAfterPutt+1)] <- putt[1:NumStrokesPutt]  
    }
    PathTakenTemp[buffer-1] <- StrokesAfterFairway + NumStrokesPutt
    PathTakenTemp[buffer] <- putt[sizeP]
    # Pick the best
    #cat("PathTakenTemp is:",PathTakenTemp,"\n")
    if(PathTakenTemp[buffer-1]<PathTaken[buffer-1]){
      PathTaken <- PathTakenTemp
    }
    #cat("PathTaken is:",PathTaken,"\n")
    
  }
  #cat("PathTaken is:",PathTaken,"\n")
  return(PathTaken)
}

