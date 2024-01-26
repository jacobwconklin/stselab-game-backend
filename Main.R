#####################3
# Definition of global variables
HoleLength <- 700L
GreenSize <- 15L # default was 20, Playing around with this.
FudgeFactor <- 20L #this is a stroke on sweetspot
Holes <- 9L 
Rule <- 1 #practical handoffs
n <-  1 # number of monte-carlo runs-  set to 1 now because I want to run one attempt for each student. 
s <- 3 #number of solver types
t <- 100 #tournament size
t_Pro <-1 # Professional tournament Size
Pen_am <-1 #Penalty for Amateur Putters
sp <- 3 # specialist tournament size (currently set to == s, but need to change if that changes)
Pro <- 1L
Am <- 2L
Spec <- 3L
Am_run <- t
Pro_run <- 1L
# spacers
stroke <- 15
buffer <- 40
head <- 7
sizeD <- 10
sizeF <- 25
sizeP <- 17
Offset <- 10L # you don't typically aim at the pin (must be less than 20) - default 15
FudgeFactor <- 5L #this is a stroke on sweetspot
Sink <- 0.5 #This hopefully ensures that the loop closes.
zone <- 5 #you can handoff to the next stage if you're within +/- 5 for rule three
GreenTransition <- 15
FairwayTransition <- HoleLength - 200

#### Moved the stuff here to avoid errors due to global vars

source("DesignPerformanceSim.R")
library(ggplot2)
library(dplyr)
library(readr)
options(scipen=999)

########
#Costs
###########
ProCost <- 10
SpecCost <- 12 # Default 12 - 
AmCost <- 1
DecompCost <- 10  # Default 10  - 
TrackCost <- 1


############################

a <- ((s^1) + 2*(s^2) + s^3)
m <- stroke*a*n #size of the data structure I need (multiply s^1 by 2 if you bring back R)


# All of the "S" runs are single player per subproblem
# All of the "T" runs are tournaments of t per subproblem
# I might do a "M" where pros are single and ams are tournis 


# #Running H arch
H_P1 <- H_Arch(HoleLength,Pro,1,Holes,n)
#H_P10 <- H_Arch(HoleLength,Pro,10,Holes,n)
#H_P100 <- H_Arch(HoleLength,Pro,100,Holes,n)
#H_A1 <- H_Arch (HoleLength,Am,1,Holes,n)
#H_A10 <- H_Arch (HoleLength,Am,10,Holes,n)
H_A100 <- H_Arch (HoleLength,Am,t,Holes,n)
#H_S1 <- H_Arch (HoleLength,Spec,1,Holes,n)
H_S3 <- H_Arch (HoleLength,Spec,sp,Holes,n)
#H_S10 <- H_Arch (HoleLength,Spec,10,Holes,n)
#H_S100 <- H_Arch (HoleLength,Spec,100,Holes,n)
#H_PM <- H_Arch (HoleLength,Pro,1,Holes,n)
#H_AM <- H_Arch (HoleLength,Am,t,Holes,n)
#H_SM <- H_Arch (HoleLength,Spec,t,Holes,n)

# #Running LP arch (Pros are always 1, Ams are always t = 50, Specs are always s=3)
# #t <- 50
# #s <- sp
LP_PPM <- LP_Arch(HoleLength,Pro,Pro,t_Pro,t_Pro,Rule,Holes,n)
LP_PAM <- LP_Arch(HoleLength,Pro,Am,t_Pro,t,Rule,Holes,n)
LP_PSM <- LP_Arch(HoleLength,Pro,Spec, t_Pro,sp,Rule,Holes,n)
LP_APM <- LP_Arch(HoleLength,Am,Pro,t,t_Pro,Rule,Holes,n)
LP_SPM <- LP_Arch(HoleLength,Spec,Pro,sp,t_Pro,Rule,Holes,n)
LP_AAM <- LP_Arch(HoleLength,Am,Am,t,t,Rule,Holes,n)
LP_SAM <- LP_Arch(HoleLength,Spec,Am,sp,t,Rule,Holes,n)
LP_ASM <- LP_Arch(HoleLength,Am,Spec,t,sp,Rule,Holes,n)
LP_SSM <- LP_Arch(HoleLength,Spec,Spec,sp,sp,Rule,Holes,n)

#LP_AA1 <- LP_Arch(HoleLength,Am,Am,1,1,Rule,Holes,n)
#LP_SS1 <- LP_Arch(HoleLength,1,1,s,s,Rule,Holes,n)

#PP,PA,PS,AP,SP,AA,SA,AS,SS
# 9 options

#Running DAP arch
DAP_PPPM <- DAP_Arch(HoleLength,Pro,Pro,Pro,t_Pro,t_Pro,t_Pro,Rule,Rule,Holes,n)
DAP_PPAM <- DAP_Arch(HoleLength,Pro,Pro,Am,t_Pro,t_Pro,t,Rule,Rule,Holes,n)
DAP_PAPM <- DAP_Arch(HoleLength,Pro,Am,Pro,t_Pro,t,t_Pro,Rule,Rule,Holes,n)
DAP_APPM <- DAP_Arch(HoleLength,Am,Pro,Pro,t,t_Pro,t_Pro,Rule,Rule,Holes,n)
DAP_PAAM <- DAP_Arch(HoleLength,Pro,Am,Am,t_Pro,t,t,Rule,Rule,Holes,n)
DAP_APAM <- DAP_Arch(HoleLength,Am,Pro,Am,t,t_Pro,t,Rule,Rule,Holes,n)
DAP_AAPM <- DAP_Arch(HoleLength,Am,Am,Pro,t,t,t_Pro,Rule,Rule,Holes,n)
DAP_AAAM <- DAP_Arch(HoleLength,Am,Am,Am,t,t,t,Rule,Rule,Holes,n)
DAP_PPSM <- DAP_Arch(HoleLength,Pro,Pro,Spec,t_Pro,t_Pro,sp,Rule,Rule,Holes,n)
DAP_PSPM <- DAP_Arch(HoleLength,Pro,Spec,Pro,t_Pro,sp,t_Pro,Rule,Rule,Holes,n)
DAP_SPPM <- DAP_Arch(HoleLength,Spec,Pro,Pro,sp,t_Pro,t_Pro,Rule,Rule,Holes,n)
DAP_PSSM <- DAP_Arch(HoleLength,Pro,Spec,Spec,t_Pro,sp,sp,Rule,Rule,Holes,n)
DAP_SPSM <- DAP_Arch(HoleLength,Spec,Pro,Spec,sp,t_Pro,sp,Rule,Rule,Holes,n)
DAP_SSPM <- DAP_Arch(HoleLength,Spec,Spec,Pro,sp,sp,t_Pro,Rule,Rule,Holes,n)
DAP_SSSM <- DAP_Arch(HoleLength,Spec,Spec,Spec,sp,sp,sp,Rule,Rule,Holes,n)
DAP_SSAM <- DAP_Arch(HoleLength,Spec,Spec,Am,sp,sp,t,Rule,Rule,Holes,n)
DAP_SASM <- DAP_Arch(HoleLength,Spec,Am,Spec,sp,t,sp,Rule,Rule,Holes,n)
DAP_ASSM <- DAP_Arch(HoleLength,Am,Spec,Spec,t,sp,sp,Rule,Rule,Holes,n)
DAP_SAAM <- DAP_Arch(HoleLength,Spec,Am,Am,sp,t,t,Rule,Rule,Holes,n)
DAP_ASAM <- DAP_Arch(HoleLength,Am,Spec,Am,t,sp,t,Rule,Rule,Holes,n)
DAP_AASM <- DAP_Arch(HoleLength,Am,Am,Spec,t,t,sp,Rule,Rule,Holes,n)
DAP_SPAM <- DAP_Arch(HoleLength,Spec,Pro,Am,sp,t_Pro,t,Rule,Rule,Holes,n)
DAP_SAPM <- DAP_Arch(HoleLength,Spec,Am,Pro,sp,t,t_Pro,Rule,Rule,Holes,n)
DAP_ASPM <- DAP_Arch(HoleLength,Am,Spec,Pro,t,sp,t_Pro,Rule,Rule,Holes,n)
DAP_APSM <- DAP_Arch(HoleLength,Am,Pro,Spec, t,t_Pro,sp,Rule,Rule,Holes,n)
DAP_PSAM <- DAP_Arch(HoleLength,Pro,Spec,Am,t_Pro,sp,t,Rule,Rule,Holes,n)
DAP_PASM <- DAP_Arch(HoleLength,Pro,Am,Spec,t_Pro,t,sp,Rule,Rule,Holes,n)
#27
#

# Running DS arch
#rep("PP",n*stroke),rep("PA",n*stroke),rep("AP",n*stroke),rep("AA",n*stroke))
DS_PPM <- DS_Arch(HoleLength,Pro,Pro,t_Pro,t_Pro,Rule,Holes,n)
DS_PAM <- DS_Arch(HoleLength,Pro,Am,t_Pro,t,Rule,Holes,n)
DS_PSM <- DS_Arch(HoleLength,Pro,Spec, t_Pro,sp,Rule,Holes,n)
DS_APM <- DS_Arch(HoleLength,Am,Pro,t,t_Pro,Rule,Holes,n)
DS_SPM <- DS_Arch(HoleLength,Spec,Pro,sp,t_Pro,Rule,Holes,n)
DS_AAM <- DS_Arch(HoleLength,Am,Am,t,t,Rule,Holes,n)
DS_SAM <- DS_Arch(HoleLength,Spec,Am,sp,t,Rule,Holes,n)
DS_ASM <- DS_Arch(HoleLength,Am,Spec,t,sp,Rule,Holes,n)
DS_SSM <- DS_Arch(HoleLength,Spec,Spec,sp,sp,Rule,Holes,n)
# 9


# This is the data structure for the results in terms of golf score.
#n <- 5
StrokeResults <- data.frame(
  Architecture = c(rep("H",n*s*3),rep("LP",n*(s^2)),rep("DAP",n*(s^3)),rep("DS",n*(s^2))),
  Assignment = c(rep("P",n*3),rep("A",n*3),rep("S",n*3),
                 rep("PP",n),rep("PA",n), rep("PS",n),rep("AP",n), rep("SP",n), rep("AA",n),rep("SA",n),rep("AS",n),rep("SS",n),
                 rep("PPP",n),rep("PPA",n),rep("PAP",n),rep("APP",n),rep("PAA",n),rep("APA",n),rep("AAP",n),rep("AAA",n),
                 rep("PPS",n),rep("PSP",n),rep("SPP",n),rep("PSS",n),rep("SPS",n),rep("SSP",n),rep("SSS",n),
                 rep("SSA",n),rep("SAS",n),rep("ASS",n),rep("SAA",n),rep("ASA",n),rep("AAS",n),
                 rep("SPA",n),rep("SAP",n),rep("ASP",n),rep("APS",n),rep("PSA",n),rep("PAS",n),
                 rep("PP",n),rep("PA",n), rep("PS",n),rep("AP",n), rep("SP",n), rep("AA",n),rep("SA",n),rep("AS",n),rep("SS",n)),
  Assignment_type = c(rep("Pro",n*3),rep("Amateur",n*3),rep("Specialist",n*3),rep("Hybrid",n*(s^2+s^3+s^2))),
  Tournament_type = c(rep(c(rep("1",n),rep("10",n),rep("100",n)),3),rep("mixed",n*(s^2+s^3+s^2))),
  Run = rep(1:n,(s*3+s^2+s^3+s^2)),
  Score = rep(0,n*(s*3+s^2+s^3+s^2)),
  Sub1 = rep(0,n*(s*3+s^2+s^3+s^2)),
  Sub2 = rep(0,n*(s*3+s^2+s^3+s^2)),
  Sub3 = rep(0,n*(s*3+s^2+s^3+s^2)),
  cost = rep(0,n*(s*3+s^2+s^3+s^2)),
  sched_steady = rep(0,n*(s*3+s^2+s^3+s^2)),
  Fraction = rep(0,n*(s*3+s^2+s^3+s^2))
)

j <- 1
h <- n
for (i in 1:n){
  StrokeResults[j,c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- H_P1[1:head,i]
  # StrokeResults[(j+h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- H_P10[1:head,i]
  # StrokeResults[(j+2*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- H_P100[1:head,i]
  # StrokeResults[j+3*h,c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- H_A1[1:head,i]
  # StrokeResults[(j+4*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- H_A10[1:head,i]
  StrokeResults[(j+5*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- H_A100[1:head,i]
  StrokeResults[j+6*h,c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- H_S3[1:head,i]
  # StrokeResults[(j+7*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- H_S10[1:head,i]
  # StrokeResults[(j+8*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- H_S100[1:head,i]
  # # LP => PP,PA,PS,AP,SP,AA,SA,AS,SS
  StrokeResults[j+9*h,c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- LP_PPM[1:head,i]
  StrokeResults[(j+10*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- LP_PAM[1:head,i]
  StrokeResults[(j+11*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- LP_PSM[1:head,i]
  StrokeResults[j+12*h,c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- LP_APM[1:head,i]
  StrokeResults[(j+13*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- LP_SPM[1:head,i]
  StrokeResults[(j+14*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- LP_AAM[1:head,i]
  StrokeResults[j+15*h,c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- LP_SAM[1:head,i]
  StrokeResults[(j+16*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- LP_ASM[1:head,i]
  StrokeResults[(j+17*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- LP_SSM[1:head,i]

  #PPP,PPA,PAP,APP,PAA,APA,AAP,AAA,PPS,PSP,SPP,PSS,SPS,SSP,SSS,SSA,SAS,ASS,SAA,ASA,AAS,SPA,SAP,ASP,APS,PSA,PAS
  StrokeResults[j+18*h,c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_PPPM[1:head,i]
  StrokeResults[(j+19*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_PPAM[1:head,i]
  StrokeResults[(j+20*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_PAPM[1:head,i]
  StrokeResults[(j+21*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_APPM[1:head,i]
  StrokeResults[j+22*h,c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_PAAM[1:head,i]
  StrokeResults[(j+23*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_APAM[1:head,i]
  StrokeResults[(j+24*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_AAPM[1:head,i]
  StrokeResults[(j+25*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_AAAM[1:head,i]

  StrokeResults[(j+26*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_PPSM[1:head,i]
  StrokeResults[(j+27*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_PSPM[1:head,i]
  StrokeResults[(j+28*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_SPPM[1:head,i]
  StrokeResults[j+29*h,c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_PSSM[1:head,i]
  StrokeResults[(j+30*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_SPSM[1:head,i]
  StrokeResults[(j+31*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_SSPM[1:head,i]
  StrokeResults[(j+32*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_SSSM[1:head,i]
  #SSA,SAS,ASS,SAA,ASA,AAS,
  StrokeResults[(j+33*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_SSAM[1:head,i]
  StrokeResults[(j+34*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_SASM[1:head,i]
  StrokeResults[(j+35*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_ASSM[1:head,i]
  StrokeResults[(j+36*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_SAAM[1:head,i]
  StrokeResults[(j+37*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_ASAM[1:head,i]
  StrokeResults[(j+38*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_AASM[1:head,i]
  # SPA,SAP,ASP,APS,PSA,PAS
  StrokeResults[(j+39*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_SPAM[1:head,i]
  StrokeResults[(j+40*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_SAPM[1:head,i]
  StrokeResults[(j+41*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_ASPM[1:head,i]
  StrokeResults[(j+42*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_APSM[1:head,i]
  StrokeResults[(j+43*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_PSAM[1:head,i]
  StrokeResults[(j+44*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DAP_PASM[1:head,i]

  # DS => PP,PA,PS,AP,SP,AA,SA,AS,SS
  StrokeResults[j+45*h,c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DS_PPM[1:head,i]
  StrokeResults[(j+46*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DS_PAM[1:head,i]
  StrokeResults[(j+47*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DS_PSM[1:head,i]
  StrokeResults[j+48*h,c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DS_APM[1:head,i]
  StrokeResults[(j+49*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DS_SPM[1:head,i]
  StrokeResults[(j+50*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DS_AAM[1:head,i]
  StrokeResults[j+51*h,c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DS_SAM[1:head,i]
  StrokeResults[(j+52*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DS_ASM[1:head,i]
  StrokeResults[(j+53*h),c('Score','Sub1','Sub2','Sub3','cost','sched_steady','Fraction')] <- DS_SSM[1:head,i]

  j <- j+1
}

write_csv(StrokeResults, path = file.path('data_output', 'PNASstrokes20200629.csv'))


## Everything below this line is for past verification and validation plots we created, no need to worry about it for the game 

# #### Order before analysis ### 
# Strokes <- StrokeResults
# Strokes$Architecture <- factor(Strokes$Architecture, level = c("H","LP","DAP","DS"))
# Strokes$Assignment_type <- factor(Strokes$Assignment_type, level = c("Pro","Amateur","Specialist","Hybrid"))
# 
# ##############################################
# #####  Add on for the Sensitivity Analysis ###
# #############################################
# 
# 
# ##### Carryover Functions for Sumstats Decomp
# 
# #This function comes from the R Cookbook
# 
# summarySE <- function(data=NULL, measurevar, groupvars=NULL, na.rm=FALSE,
#                       conf.interval=.95, .drop=TRUE) {
#   #  library(plyr) this is redundant and it might be messing things up
#   
#   # New version of length which can handle NA's: if na.rm==T, don't count them
#   length2 <- function (x, na.rm=FALSE) {
#     if (na.rm) sum(!is.na(x))
#     else       length(x)
#   }
#   
#   # This does the summary. For each group's data frame, return a vector with
#   # N, mean, and sd
#   datac <- plyr::ddply(data, groupvars, .drop=.drop,
#                        .fun = function(xx, col) {
#                          c(N    = length2(xx[[col]], na.rm=na.rm),
#                            mean = mean   (xx[[col]], na.rm=na.rm),
#                            sd   = sd     (xx[[col]], na.rm=na.rm)
#                          )
#                        },
#                        measurevar
#   )
#   
#   # Rename the "mean" column    
#   datac <- plyr::rename(datac, c("mean" = measurevar))
#   
#   datac$se <- datac$sd / sqrt(datac$N)  # Calculate standard error of the mean
#   
#   # Confidence interval multiplier for standard error
#   # Calculate t-statistic for confidence interval: 
#   # e.g., if conf.interval is .95, use .975 (above/below), and use df=N-1
#   ciMult <- qt(conf.interval/2 + .5, datac$N-1)
#   datac$ci <- datac$se * ciMult
#   
#   return(datac)
# }
######################################################

############################
# # Assessing impacts of decomposing 
# sumstatsDecomp <- summarySE(Strokes, measurevar="Score", groupvars=c("Architecture", "Assignment","Tournament_type"))
# sumcost <- summarySE(Strokes,measurevar = "cost",groupvars=c("Architecture", "Assignment","Tournament_type"))
# sumstatsDecomp$cost <- sumcost$cost
# sumstatsDecomp$cost_sd <- sumcost$sd
# sumstatsDecomp$cost_se <- sumcost$se
# 
# 
# sumFraction <- summarySE(Strokes,measurevar = "Fraction",groupvars=c("Architecture", "Assignment","Tournament_type"))
# sumstatsDecomp$Fraction <- sumFraction$Fraction
# sumschedsteady <- summarySE(Strokes,measurevar = "Sub1",groupvars=c("Architecture", "Assignment","Tournament_type"))
# sumstatsDecomp[c('Sub1','ci_1')] <- sumschedsteady[c('Sub1','ci')]
# sumschedsteady <- summarySE(Strokes,measurevar = "Sub2",groupvars=c("Architecture", "Assignment","Tournament_type"))
# sumstatsDecomp[c('Sub2','ci_2')] <- sumschedsteady[c('Sub2','ci')]
# sumschedsteady <- summarySE(Strokes,measurevar = "Sub3",groupvars=c("Architecture", "Assignment","Tournament_type"))
# sumstatsDecomp[c('Sub3','ci_3')] <- sumschedsteady[c('Sub3','ci')]
# T <- 3
# R <- 3
# sumstatsDecomp['Assignment_type'] <- c(rep('Amateur',T),rep('Pro',T),rep('Amateur',T),rep('Pro',T),rep(c(rep('Amateur',T*R),rep('Hybrid',T*R*2),rep('Pro',T*R)),2))
# #Making this seem like a three hole course for sched purposes.
# sumstatsDecomp$sched_steady[1:6] <-sumstatsDecomp$sched_steady[1:6]*3
# sumstatsDecomp$sched_part[1:6] <-sumstatsDecomp$sched_part[1:6]*3
# sumstatsDecomp$Tournament_type <- rep(c(1,10,100),28)
# ########################################################
# 
# sumstatsDecomp_sens <- filter(sumstatsDecomp, Score!= 0)
# Bench_perf <- sumstatsDecomp_sens$Score[2]
# Bench_cost <- sumstatsDecomp_sens$cost[2]
# 
# ##### Sennsitivity Table
# Dominant <- filter(sumstatsDecomp_sens,(cost<Bench_cost & Score<Bench_perf))
# write_csv(Dominant, path = file.path('data_output', 'Worse_SP_Dominant.csv'))
# 
# Dominant_fuzzy <-filter(sumstatsDecomp_sens,((Score<Bench_perf | cost<Bench_cost) & (Fraction<=0.75&cost<1.2*Bench_cost & Score<1.2*Bench_perf)))
# write_csv(Dominant_fuzzy, path = file.path('data_output', 'Worse_SP_FuzzyDominant.csv'))
# 
# Best_Pro <- filter(sumstatsDecomp_sens,(Assignment == "P"|Assignment == "PP"| Assignment == "PPP"))
# Best_Pro <- Best_Pro %>%   arrange(Score)
# write_csv(Best_Pro, path = file.path('data_output', 'Best_for_Pros.csv'))
# 
# 
# Best_Am <- filter(sumstatsDecomp_sens,(Assignment == "A"|Assignment == "AA"| Assignment == "AAA"))
# Best_Am <- Best_Am %>%   arrange(Score)
# write_csv(Best_Am, path = file.path('data_output', 'Best_for_Am.csv'))
# 
# 
# Best_Sp <- filter(sumstatsDecomp_sens,(Assignment == "S"|Assignment == "SS"| Assignment == "SSS"))
# Best_Sp <- Best_Sp %>%   arrange(Score)
# write_csv(Best_Sp, path = file.path('data_output', 'Best_for_Sp.csv'))

####################################################
# Now I'm storing the data to visualize the differences between pros and amateurs
#############################
# y <- 10000 ## this is the number of runs for the V&V plots
# x <- 7*y
# # 
# # Subproblems <- data.frame(
# #   Solver_type = c(rep("Pro",x),rep("Am",x),rep("Spec",x)),
# #   Subproblem_type = rep(c(rep("Drive",y),rep("Fairway",3*y),rep("Green",3*y)),3),
# #   distance = rep(c(rep("sixfifty",y),rep("3hundred",y),rep("2hundred",y),rep("1hundred",y),rep("twenty",y),rep("ten",y),rep("five",y)),3),
# #   Run = rep(1:y,21),
# #   Result = rep(0,3*x)
# # )
# # 
# z <- 4*y
# 
# Shots <- data.frame(
#   Solver_type = c(rep("Pro",z),rep("Am",z),rep("Spec",z)),
#   Shot_type = rep(c(rep("Tee",y),rep("LongFairway",y),rep("AimFairway",y),rep("Putt",y)),3),
#   Run = rep(1:y,12),
#   Result = rep(0,3*z)
# )
# 
# 
# for (e in 1:3){
#   for (i in 1:y){
#     DriveResult <- PlayDrive(650,e,1,1,0)
#     Subproblems$Result[(x*(e-1)+i)] <- DriveResult[sizeD-1]
#     FairwayResult <- PlayFairway(300,e,1,1,0)
#     Subproblems$Result[(x*(e-1)+i+y)] <- FairwayResult[sizeF-1]+1
#     FairwayResult <- PlayFairway(200,e,1,1,0)
#     Subproblems$Result[(x*(e-1)+2*i+y)] <- FairwayResult[sizeF-1]+1
#     FairwayResult <- PlayFairway(100,e,1,1,0)
#     Subproblems$Result[(x*(e-1)+3*i+y)] <- FairwayResult[sizeF-1]+1
#     PuttResult <- PlayPutt(20,e,1,0.2)
#     Subproblems$Result[(x*(e-1)+i+4*y)] <- PuttResult[sizeP-1]+1
#     PuttResult <- PlayPutt(10,e,1,0.2)
#     Subproblems$Result[(x*(e-1)+i+5*y)] <- PuttResult[sizeP-1]+1
#     PuttResult <- PlayPutt(5,e,1,0.2)
#     Subproblems$Result[(x*(e-1)+i+6*y)] <- PuttResult[sizeP-1]+1
#     
#     Shots$Result[(z*(e-1)+i)] <- 650-Drive(650,e,0,1)
#     Shots$Result[(z*(e-1)+i+y)] <- LFairway(300,e,0,1)
#     Shots$Result[(z*(e-1)+i+2*y)] <- AFairway(100,e,1,0)
#     Shots$Result[(z*(e-1)+i+3*y)] <- Putt(10,e,1)
#   }
# }
# write_csv(Subproblems, path = file.path('data_output', 'PNASsubproblems20200703.csv'))
# write_csv(Shots, path = file.path('data_output', 'PNASshots20200703.csv'))


# #######################
# # Verification runs: you need to uncomment this and the ys and zs above to do the V&V runs
# #######################
# 
# VandV <- data.frame(
#   Solver = c(rep("Pro",z),rep("Am",z),rep("Spec",z),rep("Am",8*y)),
#   Architecture = c(rep(c(rep("H",y),rep("DS",y),rep("LP",y),rep("DFP",y)),3),rep("H",8*y)),
#   Size = rep(c(rep("1",3*z),rep("10",y),rep("50",y),rep("100",y),rep("500",y),rep("1000",y),rep("2500",y),rep("5000",y),rep("10000",y))),
#   Run = rep(1:y,20),
#   Result = rep(0,20*(y))
# )

# 
# VandV <- data.frame(
#   Solver = c(rep("Pro",z),rep("Am",z),rep("Spec",z),rep("Am",4*y),rep("Spec",4*y)),
#   Architecture = c(rep(c(rep("H",y),rep("DS",y),rep("LP",y),rep("DFP",y)),3),rep("H",y),rep("DS",y),rep("LP",y),rep("DFP",y),rep("H",y),rep("DS",y),rep("LP",y),rep("DFP",y)),
#   Size = rep(c(rep("1",3*z),rep("100",4*y),rep("3",4*y))),
#   Run = rep(1:y,20),
#   Result = rep(0,20*(y))
# )
# 
# for (e in 1:3){
#   for (i in 1:y){
#     H <- H_Arch(HoleLength,e,1,Holes,1)
#     VandV$Result[(z*(e-1)+i)] <- H[1]
#     DS <- DS_Arch(HoleLength,e,e,1,1,Rule,Holes,1)
#     VandV$Result[(z*(e-1)+i+y)] <- DS[1]
#     LP <- LP_Arch(HoleLength,e,e,1,1,Rule,Holes,1)
#     VandV$Result[(z*(e-1)+i+2*y)] <- LP[1]
#     DFP <- DAP_Arch(HoleLength,e,e,e,1,1,1,Rule,Rule,Holes,1)
#     VandV$Result[(z*(e-1)+i+3*y)] <- DFP[1]
#     H100 <- H_Arch(HoleLength,2,100,Holes,1)
#     VandV$Result[(y*12+i)] <- H100[1]
#     DS_Amat <- DS_Arch(HoleLength,2,2,t,t,Rule,Holes,1)
#     VandV$Result[(y*12+i+y)] <- DS_Amat[1]
#     LP_Amat <- LP_Arch(HoleLength,2,2,t,t,Rule,Holes,1)
#     VandV$Result[(y*12+i+2*y)] <- LP_Amat[1]
#     DFP_Amat <- DAP_Arch(HoleLength,2,2,2,t,t,t,Rule,Rule,Holes,1)
#     VandV$Result[(y*12+i+3*y)] <- DFP_Amat[1]
#     H_Sp <- H_Arch(HoleLength,3,3,Holes,1)
#     VandV$Result[(y*12+i+4*y)] <- H_Sp[1]
#     DS_Sp <- DS_Arch(HoleLength,3,3,3,3,Rule,Holes,1)
#     VandV$Result[(y*12+i+5*y)] <- DS_Sp[1]
#     LP_Sp <- LP_Arch(HoleLength,3,3,3,3,Rule,Holes,1)
#     VandV$Result[(y*12+i+6*y)] <- LP_Sp[1]
#     DFP_Sp <- DAP_Arch(HoleLength,3,3,3,3,3,3,Rule,Rule,Holes,1)
#     VandV$Result[(y*12+i+7*y)] <- DFP_Sp[1]
#     
#     
#     
#     # 
#     # H10 <- H_Arch(HoleLength,2,10,Holes,1)
#     # VandV$Result[(y*12+i)] <- H10[1]
#     # H50 <- H_Arch(HoleLength,2,50,Holes,1)
#     # VandV$Result[(y*12+i+y)] <- H50[1]
#     # H100 <- H_Arch(HoleLength,2,100,Holes,1)
#     # VandV$Result[(y*12+i+2*y)] <- H100[1]
#     # H500 <- H_Arch(HoleLength,2,500,Holes,1)
#     # VandV$Result[(y*12+i+3*y)] <- H500[1]
#     # H1000 <- H_Arch(HoleLength,2,1000,Holes,1)
#     # VandV$Result[(y*12+i+4*y)] <- H1000[1]
#     # H2500 <- H_Arch(HoleLength,2,2500,Holes,1)
#     # VandV$Result[(y*12+i+5*y)] <- H2500[1]
#     # H5000 <- H_Arch(HoleLength,2,5000,Holes,1)
#     # VandV$Result[(y*12+i+6*y)] <- H5000[1]
#     # H10000 <- H_Arch(HoleLength,2,10000,Holes,1)
#     # VandV$Result[(y*12+i+7*y)] <- H10000[1]
#     # DS_Amat <- DS_Arch(HoleLength,2,2,t,t,Rule,Holes,1)
#     # VandV$Result[(y*12+i+8*y)] <- DS_Amat[1]
#     # LP_Amat <- LP_Arch(HoleLength,2,2,t,t,Rule,Holes,1)
#     # VandV$Result[(y*12+i+9*y)] <- LP_Amat[1]
#     # DFP_Amat <- DAP_Arch(HoleLength,2,2,2,t,t,t,Rule,Rule,Holes,1)
#     # VandV$Result[(y*12+i+10*y)] <- DFP_Amat[1]
#     # H_Sp <- H_Arch(HoleLength,3,3,Holes,1)
#     # VandV$Result[(y*12+i+11*y)] <- H_Sp[1]
#     # DS_Sp <- DS_Arch(HoleLength,3,3,3,3,Rule,Holes,1)
#     # VandV$Result[(y*12+i+12*y)] <- DS_Sp[1]
#     # LP_Sp <- LP_Arch(HoleLength,3,3,3,3,Rule,Holes,1)
#     # VandV$Result[(y*12+i+13*y)] <- LP_Sp[1]
#     # DFP_Sp <- DAP_Arch(HoleLength,3,3,3,3,3,3,Rule,Rule,Holes,1)
#     # VandV$Result[(y*12+i+14*y)] <- DFP_Sp[1]
#   }
# }
# 
# write_csv(VandV, path = file.path('data_output', 'PNASVandV20200721.csv'))
# 
# # #######################################################
# # ##### Verification 2, for 3 Sps and 100 Amateurs ######
# # #######################################################
# 
# 
# VandV2 <- data.frame(
#   Solver = c(rep("Pro",z),rep("Am",z),rep("Spec",z)),
#   Architecture = c(rep(c(rep("H",y),rep("DS",y),rep("LP",y),rep("DFP",y)),3)),
#   Size = rep(c(rep("1",z),rep("100",z),rep("3",z))),
#   Run = rep(1:y,12),
#   Result = rep(0,12*(y))
# )
# 
# 
# for (i in 1:y){
#     H_Pro <- H_Arch(HoleLength,1,1,Holes,1)
#     VandV2$Result[(i)] <- H_Pro[1]
#     DS_Pro <- DS_Arch(HoleLength,1,1,1,1,Rule,Holes,1)
#     VandV2$Result[y+i] <- DS_Pro[1]
#     LP_Pro <- LP_Arch(HoleLength,1,1,1,1,Rule,Holes,1)
#     VandV2$Result[2*y+i] <- LP_Pro[1]
#     DFP_Pro <- DAP_Arch(HoleLength,1,1,1,1,1,1,Rule,Rule,Holes,1)
#     VandV2$Result[3*y+i] <-  DFP_Pro[1]
#     H_Am <- H_Arch(HoleLength,2,100,Holes,1)
#     VandV2$Result[4*y+i] <- H_Am[1]
#     DS_Am <- DS_Arch(HoleLength,2,2,100,100,Rule,Holes,1)
#     VandV2$Result[5*y+i] <- DS_Am[1]
#     LP_Am <- LP_Arch(HoleLength,2,2,100,100,Rule,Holes,1)
#     VandV2$Result[6*y+i] <- LP_Am[1]
#     DFP_Am <- DAP_Arch(HoleLength,2,2,2,100,100,100,Rule,Rule,Holes,1)
#     VandV2$Result[7*y+i] <-  DFP_Am[1]
#     H_Sp <- H_Arch(HoleLength,3,3,Holes,1)
#     VandV2$Result[8*y+i] <- H_Sp[1]
#     DS_Sp <- DS_Arch(HoleLength,3,3,3,3,Rule,Holes,1)
#     VandV2$Result[9*y+i] <- DS_Sp[1]
#     LP_Sp <- LP_Arch(HoleLength,3,3,3,3,Rule,Holes,1)
#     VandV2$Result[10*y+i] <- LP_Sp[1]
#     DFP_Sp <- DAP_Arch(HoleLength,3,3,3,3,3,3,Rule,Rule,Holes,1)
#     VandV2$Result[11*y+i] <-  DFP_Sp[1]
#     }
# 
# write_csv(VandV2, path = file.path('data_output', 'Verification2.csv'))
