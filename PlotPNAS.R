library(ggplot2)
library(readr)
library(ggThemeAssist)
library(datasets)
library(fcuk)
library(plyr)
library(dplyr)
library(ggpubr)
library(cowplot)
library(reshape)
library(tidyr)

Strokes <- read_csv(file.path('data_output', 'PNASStrokes20200629.csv'))
# Subproblems <- read_csv(file.path('data_output', 'PNASSubproblems20200703.csv'))
# Shots <- read_csv(file.path('data_output', 'PNASshots20200703.csv'))
# VandV <- read_csv(file.path('data_output', 'PNASVandV20200721.csv'))
# VandV2 <- read_csv(file.path('data_output', 'Verification2.csv'))
# Isos_Am <- read_csv(file.path('data_output', 'AmateurSweep.csv')) # read the iso file
# Isos_Pro <- read_csv(file.path('data_output', 'ProSweep.csv')) # read the iso file  for Pros

### Controlling order that they appear in charts.
Strokes$Architecture <- factor(Strokes$Architecture, level = c("H","LP","DAP","DS"))
Strokes$Assignment_type <- factor(Strokes$Assignment_type, level = c("Pro","Amateur","Specialist","Hybrid"))
# Subproblems$Solver_type <- factor(Subproblems$Solver_type, level = c("Pro","Am","Spec"))
# Shots$Solver_type <- factor(Shots$Solver_type, level = c("Pro","Am","Spec"))
# Shots$Shot_type <- factor(Shots$Shot_type, level = c("Tee","LongFairway","AimFairway","Putt"))
# VandV$Solver <- factor(VandV$Solver, level = c("Pro","Am","Spec"))
# VandV$Architecture <- factor(VandV$Architecture, level = c("H","DS","LP","DFP"))
# VandV2$Solver <- factor(VandV2$Solver, level = c("Pro","Am","Spec"))
# VandV2$Architecture <- factor(VandV2$Architecture, level = c("H","DS","LP","DFP"))
######################3

#This function comes from the R Cookbook

summarySE <- function(data=NULL, measurevar, groupvars=NULL, na.rm=FALSE,
                      conf.interval=.95, .drop=TRUE) {
#  library(plyr) this is redundant and it might be messing things up
  
  # New version of length which can handle NA's: if na.rm==T, don't count them
  length2 <- function (x, na.rm=FALSE) {
    if (na.rm) sum(!is.na(x))
    else       length(x)
  }
  
  # This does the summary. For each group's data frame, return a vector with
  # N, mean, and sd
  datac <- plyr::ddply(data, groupvars, .drop=.drop,
                 .fun = function(xx, col) {
                   c(N    = length2(xx[[col]], na.rm=na.rm),
                     mean = mean   (xx[[col]], na.rm=na.rm),
                     sd   = sd     (xx[[col]], na.rm=na.rm)
                   )
                 },
                 measurevar
  )
  
  # Rename the "mean" column    
  datac <- plyr::rename(datac, c("mean" = measurevar))
  
  datac$se <- datac$sd / sqrt(datac$N)  # Calculate standard error of the mean
  
  # Confidence interval multiplier for standard error
  # Calculate t-statistic for confidence interval: 
  # e.g., if conf.interval is .95, use .975 (above/below), and use df=N-1
  ciMult <- qt(conf.interval/2 + .5, datac$N-1)
  datac$ci <- datac$se * ciMult
  
  return(datac)
}
######################################################

############################
# Assessing impacts of decomposing 
sumstatsDecomp <- summarySE(Strokes, measurevar="Score", groupvars=c("Architecture", "Assignment","Tournament_type"))
sumcost <- summarySE(Strokes,measurevar = "cost",groupvars=c("Architecture", "Assignment","Tournament_type"))
sumstatsDecomp$cost <- sumcost$cost
sumstatsDecomp$cost_sd <- sumcost$sd
sumstatsDecomp$cost_se <- sumcost$se


sumFraction <- summarySE(Strokes,measurevar = "Fraction",groupvars=c("Architecture", "Assignment","Tournament_type"))
sumstatsDecomp$Fraction <- sumFraction$Fraction
sumschedsteady <- summarySE(Strokes,measurevar = "Sub1",groupvars=c("Architecture", "Assignment","Tournament_type"))
sumstatsDecomp[c('Sub1','ci_1')] <- sumschedsteady[c('Sub1','ci')]
sumschedsteady <- summarySE(Strokes,measurevar = "Sub2",groupvars=c("Architecture", "Assignment","Tournament_type"))
sumstatsDecomp[c('Sub2','ci_2')] <- sumschedsteady[c('Sub2','ci')]
sumschedsteady <- summarySE(Strokes,measurevar = "Sub3",groupvars=c("Architecture", "Assignment","Tournament_type"))
sumstatsDecomp[c('Sub3','ci_3')] <- sumschedsteady[c('Sub3','ci')]
T <- 3
R <- 3
sumstatsDecomp['Assignment_type'] <- c(rep('Amateur',T),rep('Pro',T),rep('Amateur',T),rep('Pro',T),rep(c(rep('Amateur',T*R),rep('Hybrid',T*R*2),rep('Pro',T*R)),2))
#Making this seem like a three hole course for sched purposes.
sumstatsDecomp$sched_steady[1:6] <-sumstatsDecomp$sched_steady[1:6]*3
sumstatsDecomp$sched_part[1:6] <-sumstatsDecomp$sched_part[1:6]*3
sumstatsDecomp$Tournament_type <- rep(c(1,10,100),28)
########################################################
####### Calculations for the Design Science Figures ######
#########################################################

######################################################### get PP vs PA on LG 
LG_PAvsPP = subset(sumstatsDecomp, (Architecture== "LP" & (Assignment == "PA" | Assignment == "PP"| Assignment == "PS"  )))


# R= (q − wc ∗ c)
LG_PAvsPP_test <-  LG_PAvsPP %>%   mutate(Reward_wc1_Viktranth = Score-cost)
LG_PAvsPP_test <-  LG_PAvsPP_test %>%   mutate(Reward_wc1_Sum = Score+cost)



LG_PAvsPP_test <- LG_PAvsPP_test[c(-3,-4,-6,-7,-8,-10,-11,-12,-13,-14,-15,-16,-17,-18)] ## Drops sub scores we don't need them for now - this gets rids of steady too

LG_PAvsPP_test_long <- gather(LG_PAvsPP_test, outcome_variable, value, Score:Reward_wc1_Sum) ## convert to long format for boxplots
#Strokes_Clean_draft$outcome_variable <- factor(Strokes_Clean_draft$outcome_variable, levels = c( "Performance", "Cost","Schedule")) 




IncFigure_testjoint <- ggplot(LG_PAvsPP_test_long)+
  theme_bw()+  
  #  geom_hline(yintercept = 0)+
  #  geom_text(aes(x = 0, y = 0, label = "AAPL")) + 
  #  annotate("text", label = "Pro Benchmark", x = 1, y = 2) +
  #  annotate(geom = "text", x = 4.1, y = 0, label = "Pro Benchmark", hjust = "left")+
  #  geom_text(aes(x=0, y=0, label="Pro Benchmark"), color="orange",size=7 , angle=45, fontface="bold" )+
  #  geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Assignment, y = value, color=outcome_variable))+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Reward function Comparison on LG") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Performance")+
  xlab("Assignment") 
IncFigure_testjoint
ggsave(IncFigure, filename = file.path('Figures', 'IncFigure.png'),width = 6,height = 6,dpi = 1200)




IncFigure <- ggplot(LG_PAvsPP)+
  theme_bw()+  
  #  geom_hline(yintercept = 0)+
  #  geom_text(aes(x = 0, y = 0, label = "AAPL")) + 
  #  annotate("text", label = "Pro Benchmark", x = 1, y = 2) +
  #  annotate(geom = "text", x = 4.1, y = 0, label = "Pro Benchmark", hjust = "left")+
  #  geom_text(aes(x=0, y=0, label="Pro Benchmark"), color="orange",size=7 , angle=45, fontface="bold" )+
  #  geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Assignment, y = Score))+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Score Comparison on LG") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Performance")+
  xlab("Assignment") 
IncFigure
ggsave(IncFigure, filename = file.path('Figures', 'IncFigure.png'),width = 6,height = 6,dpi = 1200)

IncFigureReward <- ggplot(LG_PAvsPP_test)+
  theme_bw()+  
  #  geom_hline(yintercept = 0)+
  #  geom_text(aes(x = 0, y = 0, label = "AAPL")) + 
  #  annotate("text", label = "Pro Benchmark", x = 1, y = 2) +
  #  annotate(geom = "text", x = 4.1, y = 0, label = "Pro Benchmark", hjust = "left")+
  #  geom_text(aes(x=0, y=0, label="Pro Benchmark"), color="orange",size=7 , angle=45, fontface="bold" )+
  #  geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Assignment, y = Reward_wc1_Viktranth))+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Vikranth Reward - Wc= 1") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Performance")+
  xlab("Assignment") 
IncFigureReward
ggsave(IncFigureReward, filename = file.path('Figures', 'IncFigureReward.png'),width = 6,height = 6,dpi = 1200)


IncFigureReward_ters <- ggplot(LG_PAvsPP_test)+
  theme_bw()+  
  #  geom_hline(yintercept = 0)+
  #  geom_text(aes(x = 0, y = 0, label = "AAPL")) + 
  #  annotate("text", label = "Pro Benchmark", x = 1, y = 2) +
  #  annotate(geom = "text", x = 4.1, y = 0, label = "Pro Benchmark", hjust = "left")+
  #  geom_text(aes(x=0, y=0, label="Pro Benchmark"), color="orange",size=7 , angle=45, fontface="bold" )+
  #  geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Assignment, y = Reward_wc1_Sum))+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Reverse Reward for Wc= 1") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Performance")+
  xlab("Assignment") 
IncFigureReward_ters
ggsave(IncFigureReward_ters, filename = file.path('Figures', 'IncFigureReward_ters.png'),width = 6,height = 6,dpi = 1200)


Sasareward <- ggarrange(IncFigure, IncFigureReward, IncFigureReward_ters,
                     labels = c("Score", "Vikranth","Reverse"),
                     ncol = 3)
Sasareward
ggsave(Sasareward, filename = file.path('Figures', 'Sasareward.png'),width = 12,height = 6, dpi = 1600)


levels(sumstatsDecomp$Architecture)[levels(sumstatsDecomp$Architecture)=="DAP"] <- "DAG"
levels(sumstatsDecomp$Architecture)[levels(sumstatsDecomp$Architecture)=="LP"] <- "LG"


sumstatsDecomp["Reference_Strat"]<-0 ## this writes the reference S assignment for the specific Decomp+Arch combination
sumstatsDecomp <-  sumstatsDecomp %>%
  mutate(Reference_Strat = ifelse((Architecture=="DAG"),paste0("S",substr(Assignment,2,3)), ifelse((Architecture=="DS"),paste0("S",substr(Assignment,2,2)),0)))

sumstatsDecomp["Reference_Label"]<-0
sumstatsDecomp <-  sumstatsDecomp %>%
  mutate(Reference_Label = ifelse((Architecture=="DAG"),paste0("X",substr(Assignment,2,3)), ifelse((Architecture=="DS"),paste0("X",substr(Assignment,2,2)),0)))

sumstatsDecomp["Delta_Label"]<-0
sumstatsDecomp <-  sumstatsDecomp %>%
  mutate(Delta_Label = ifelse(((Architecture=="DAG")&(substr(Assignment,1,1)=="A")),"Amateur", ifelse(((Architecture=="DAG")&(substr(Assignment,1,1)=="P")),"Pro", 
                                                                                                      ifelse(((Architecture=="DS")&(substr(Assignment,1,1)=="A")),"Amateur", ifelse(((Architecture=="DS") & (substr(Assignment,1,1)=="P")),"Pro",0)))))

sumstatsDecomp["Reference_Green_Strat"]<-0 ## this writes the reference Amateur assignment for the specific Decomp+Arch combination
sumstatsDecomp <-  sumstatsDecomp %>%
  mutate(Reference_Green_Strat = ifelse((Architecture=="DAG"),paste0(substr(Assignment,1,2),"A"), ifelse((Architecture=="LG"),paste0(substr(Assignment,1,1),"A"),0)))

sumstatsDecomp["Reference_Green_Label"]<-0
sumstatsDecomp <-  sumstatsDecomp %>%
  mutate(Reference_Green_Label = ifelse((Architecture=="DAG"),paste0(substr(Assignment,1,2),"X"), ifelse((Architecture=="LG"),paste0(substr(Assignment,1,1),"X"),0)))

sumstatsDecomp["Delta_Green_Label"]<-0
sumstatsDecomp <-  sumstatsDecomp %>%
  mutate(Delta_Green_Label = ifelse(((Architecture=="DAG")&(substr(Assignment,3,3)=="S")),"Specialist", ifelse(((Architecture=="DAG")&(substr(Assignment,3,3)=="P")),"Pro", 
                                                                                                               ifelse(((Architecture=="LG")&(substr(Assignment,2,2)=="S")),"Specialist", ifelse(((Architecture=="LG") & (substr(Assignment,2,2)=="P")),"Pro",0)))))

sumstatsDecomp["Ref_Score"]<-0
sumstatsDecomp["Ref_Cost"]<-0
sumstatsDecomp["Ref_Green_Score"]<-0
sumstatsDecomp["Ref_Green_ExpertReliance"]<-0

levels(VandV2$Architecture)[levels(VandV2$Architecture)=="DFP"] <- "TFG"
levels(VandV2$Architecture)[levels(VandV2$Architecture)=="DS"] <- "TS"
levels(VandV2$Architecture)[levels(VandV2$Architecture)=="LP"] <- "LG"


levels(sumstatsDecomp$Architecture)[levels(sumstatsDecomp$Architecture)=="DAG"] <- "TFG"
levels(sumstatsDecomp$Architecture)[levels(sumstatsDecomp$Architecture)=="DS"] <- "TS"
levels(sumstatsDecomp$Architecture)[levels(sumstatsDecomp$Architecture)=="LP"] <- "LG"


la2 <- filter(sumstatsDecomp, (Architecture == "TFG" |Architecture == "TS")) ## select the dataset for Specialist assignment
la3 <- filter(sumstatsDecomp, (Architecture == "TFG" |Architecture == "LG")) ## select the dataset for Green


for(i in 1: nrow(la2)){
  sec_ref_Strat <- la2$Reference_Strat[i]
  Sec <- which(la2$Assignment ==sec_ref_Strat) ## select the row number for the reference
  la2$Ref_Score[i] <- la2$Score[Sec]
  la2$Ref_Cost[i] <- la2$cost[Sec]
}

la2["Percent_Improv"]<-0
la2["Percent_Improv_Cost"]<-0
for(i in 1: nrow(la2)){
  la2$Percent_Improv[i] <- ((la2$Score[i]-la2$Ref_Score[i])/la2$Score[i])
  la2$Percent_Improv_Cost[i] <- ((la2$cost[i]-la2$Ref_Cost[i] )/la2$cost[i])
}

for(i in 1: nrow(la3)){
  sec_ref_green_Strat <- la3$Reference_Green_Strat[i]
  Sec_Green <- which(la3$Assignment ==sec_ref_green_Strat) ## select the row number for the reference
  la3$Ref_Green_Score[i] <- la3$Score[Sec_Green]
  la3$Ref_Green_ExpertReliance[i] <- la3$Fraction[Sec_Green]
}

la3["Percent_Green_Improv"]<-0 ## relative improvement of amateur assignment
la3["Percent_Green_Improv_Fraction"]<-0 ## relative improvement of amateur assignment

for(i in 1: nrow(la3)){
  la3$Percent_Green_Improv[i] <- ((la3$Score[i]-la3$Ref_Green_Score[i])/la3$Score[i])
  la3$Percent_Green_Improv_Fraction[i] <- ((la3$Fraction[i]-la3$Ref_Green_ExpertReliance[i])/la3$Fraction[i])
}
la3[is.na(la3)] <- 0
######################################3
### V&V####
###########################
# Plot single X playing each architecture

Verification <- filter(VandV,Size == "1")
## Change the name of DFP to DAP
#levels(Verification$Architecture)[levels(Verification$Architecture)=="DFP"] <- "DAP"


levels(Verification$Architecture)[levels(Verification$Architecture)=="DFP"] <- "TFG"
levels(Verification$Architecture)[levels(Verification$Architecture)=="DS"] <- "TS"
levels(Verification$Architecture)[levels(Verification$Architecture)=="LP"] <- "LG"


VePlot <- ggplot(Verification) +
  theme_bw()+
  geom_boxplot(aes(x = Architecture, y = Result))+
  facet_grid(cols = vars(Solver))+
  ggtitle("Verification - Relative Solver Performances") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14,face="bold"), strip.text.x = element_text(size = 14))+
  xlab("Problem Architecture") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Score")

VePlot
ggsave(VePlot, filename = file.path('Figures', 'Verification.png'),width = 6,height = 6, dpi = 1200)


############### Verification Plot 2 100 Ams, 3 Sps #############
## Change the name of DFP to DAP
#levels(VandV2$Architecture)[levels(VandV2$Architecture)=="DFP"] <- "DAP"
Figure6_dat <- filter(VandV,((Solver== "Pro" & Size == "1")|(Solver== "Am" & Size == "100")|(Solver== "Spec" & Size == "3"))) 
levels(Figure6_dat$Architecture)[levels(Figure6_dat$Architecture)=="DFP"] <- "TFG"
levels(Figure6_dat$Architecture)[levels(Figure6_dat$Architecture)=="DS"] <- "TS"
levels(Figure6_dat$Architecture)[levels(Figure6_dat$Architecture)=="LP"] <- "LG"


VePlot2 <- ggplot(Figure6_dat) +
  theme_bw()+
  geom_boxplot(aes(x = Architecture, y = Result))+
  facet_grid(cols = vars(Solver))+
  ggtitle("Solver Performance on Different Architectures") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14,face="bold"), strip.text.x = element_text(size = 14))+
  xlab("Problem Architecture") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Score")

VePlot2
ggsave(VePlot2, filename = file.path('Figures', 'Verification2.png'),width = 6,height = 6, dpi = 1200)

#### New Fig6

sumstats_Fig6 <- summarySE(Figure6_dat, measurevar="Result", groupvars=c("Architecture", "Solver","Size"))
sumstats_Fig6 <- sumstats_Fig6 %>% arrange(Solver) 

Ref_H_Base_Pro <- sumstats_Fig6$Result[1]
Ref_H_Base_Am <- sumstats_Fig6$Result[5]
Ref_H_Base_Sp <- sumstats_Fig6$Result[9]

sumstats_Fig6_Select <- filter(sumstats_Fig6, Architecture != "H")

sumstats_Fig6_Select$Ref_H_Base <- 0
sumstats_Fig6_Select$Ref_H_Base[1:3] <-Ref_H_Base_Pro
sumstats_Fig6_Select$Ref_H_Base[4:6] <-Ref_H_Base_Am
sumstats_Fig6_Select$Ref_H_Base[7:9] <-Ref_H_Base_Sp

sumstats_Fig6_Select$NormImp <- 0

for(i in 1: nrow(sumstats_Fig6_Select)){
  sumstats_Fig6_Select$NormImp[i] <- sumstats_Fig6_Select$Result[i] - sumstats_Fig6_Select$Ref_H_Base[i]
}


New_Fig_6 <- ggplot(sumstats_Fig6_Select, aes(x = Architecture, y = NormImp))+
  theme_bw()+
  geom_hline(yintercept = 0,size=1)+
  geom_errorbar(aes(ymin=NormImp-ci, ymax=NormImp+ci),
                width=0.2, size=0.5, color = "black")+
  geom_point(size = 0.75, shape=21, color = "black", fill = "white")+ 
  facet_grid(cols = vars(Solver))+
  #  geom_smooth(method = lm)+
  #geom_smooth()
  #geom_ribbon(aes(x = Size, y = Result, ymin = Result-ci, ymax = Result+ci))
  ggtitle("Solver Performance on Different Architectures")+
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14,face="bold"), strip.text.x = element_text(size = 14))+
  # ylab("Change (1-score/Pmean)")
  ylab("Performance w.r.t. Undecomposed Problem H")
New_Fig_6
ggsave(New_Fig_6, filename = file.path('Figures', 'New_Fig_6.png'),width = 6,height = 6, dpi = 1200)


# 
# VePlot2 <- ggplot(VandV2) +
#   theme_bw()+
#   geom_boxplot(aes(x = Architecture, y = Result))+
#   facet_grid(cols = vars(Solver))+
#   ggtitle("Solver Performance on Different Architectures") +
#   theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
#         axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
#         strip.text.y = element_text(size = 14,face="bold"), strip.text.x = element_text(size = 14))+
#   xlab("Problem Architecture") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Score")
# 
# VePlot2
# ggsave(VePlot2, filename = file.path('Figures', 'Verification2.png'),width = 6,height = 6, dpi = 1200)
# 


##### Validation Plot #########
sumstatsVandV <- summarySE(VandV, measurevar="Result", groupvars=c("Architecture", "Solver","Size"))

Validation <- filter(sumstatsVandV, Solver == "Am"&Architecture == "H")
Validation$Size <- as.numeric(Validation$Size)

Validation <- Validation %>% arrange(desc(Result))
#Validation$Size <- factor(Validation$Size, level = c("1","10","50","100","500","1000","2500","5000","10000"))

VaPlot <- ggplot(Validation, aes(x = Size, y = Result, group = 1))+
  theme_bw()+
  geom_hline(yintercept = sumstatsVandV$Result[1],size=1)+
  geom_errorbar(aes(ymin=Result-5*ci, ymax=Result+5*ci),
                width=200, size=0.9, color = "blue")+
  geom_line()+
  geom_point(size = 1, shape=21, color = "blue", fill="white")+ 
#  geom_smooth(method = lm)+
  #geom_smooth()
  #geom_ribbon(aes(x = Size, y = Result, ymin = Result-ci, ymax = Result+ci))
  ggtitle("Amateur Tournaments vs. a Single Professional")+
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"))+
  xlab("Tournament Size") +
  # ylab("Change (1-score/Pmean)")
  ylab("Score")+
  xlim(0,10000) #Default was 100
VaPlot
ggsave(VaPlot, filename = file.path('Figures', 'Validation.png'),width = 6,height = 6, dpi = 1200)
#######################
# Figure 1 - This is an "expert" problem
#####################

StrokesH <- filter(Strokes, Architecture == "H")
mean <- sumstatsDecomp$Score[4]
mean_cost <- sumstatsDecomp$cost[4]
meanP100 <- sumstatsDecomp$Score[6] -mean
StrokesH$Score <- StrokesH$Score - mean

Figure1 <- ggplot(StrokesH)+
  geom_hline(yintercept = 0)+
  geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x=Tournament_type,y=Score,color = Assignment_type))+
  ggtitle("Impact of extra effort by solver type") +
  xlab("Effort (number of solvers)") +
  ylab("Difference in performance (compared to single pro)")+
  labs(color = "Solver type")
facet_grid(cols = vars(Assignment_type))
Figure1

########################
# Figure11 - Parameter Sweep for Sink and Field Length
#######################
Isos_Am <- select(Isos_Am,-('cost'),-('Solver_type'),-(Subproblem_type)) # Discarding cost here because it is not needed.
sumstatsIsos_Am <- summarySE(Isos_Am, measurevar="Result", groupvars=c("Hole_distance", "Sink_Probability","Tournament_Size"))
#sumstatsIsos_Am_650 <- filter(sumstatsIsos_Am, Hole_distance == 650)
Isos_Pro<- select(Isos_Pro,-('Tournament_Size'))
sumstatsPro <- summarySE(Isos_Pro, measurevar="Result", groupvars=c("Hole_distance", "Sink_Probability"))
sumstatsIsos_Am["ProScore"]<-0
## Writing a small loop here to write in accurate Pro Scores for each run
bs<- 0
for (i in 1:nrow(sumstatsPro)){
  for(j in 1:4){
    sumstatsIsos_Am$ProScore[bs+j]<-sumstatsPro$Result[i]  
  }
  bs<- bs+4 #change this depending on the increments of results (how many levels of sensitivity)  
  
}
sumstatsIsos_Am["Normalized"]<-0
for (i in 1:nrow(sumstatsIsos_Am)){
  sumstatsIsos_Am$Normalized[i] <- sumstatsIsos_Am$Result[i] - sumstatsIsos_Am$ProScore[i]
  
}

# Figure_IsoField_650 <- ggplot(sumstatsIsos_Am_650,aes(x = Tournament_Size, y = Result, group = Sink_Probability, color= Sink_Probability))+
# #  geom_point()+
# #  geom_errorbar(aes(x = Tournament_Size, ymin=Result-ci, ymax=Result+ci, color= Sink_Probability),
# #                width=.5, color = "blue")+
# #  geom_line()+
#   stat_smooth()+
#   geom_point()+
#   labs(color = "Sink")+
#   geom_hline(yintercept = ave(Isos_Pro$Result[1901:2000]))+
#   ggtitle("Sensitivity of Sink Probability - 650 Yard Field") +
#   theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
#         axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
#         strip.text.y = element_text(size = 14))+
#   xlab("Tournament Size") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Score")
# Figure_IsoField_650


# Figure_IsoField <- ggplot(sumstatsIsos_Am,aes(x = Tournament_Size, y = Result, group = Sink_Probability, color= Sink_Probability))+
#   #  ggplot(sumstatsIsos_Am,aes(x = Tournament_Size, y = Result, group = Sink_Probability, color= Sink_Probability))+
#   #  geom_point()+
#   #  geom_errorbar(aes(x = Tournament_Size, ymin=Result-ci, ymax=Result+ci, color= Sink_Probability),
#   #                width=.5, color = "blue")+
#   #  geom_line()+
#   stat_smooth()+
#   geom_point()+
#   labs(color = "Sink")+
#   facet_grid(cols= vars(Hole_distance),scales = "free", space = "free")+
#   geom_hline(aes(yintercept = ProScore, color= Sink_Probability))+
#   ggtitle("Sensitivity to Sink Probability & Field Length") +
#   theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
#         axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
#         strip.text.y = element_text(size = 14))+
#   xlab("Tournament Size") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Score")
# #  geom_hline(sumstatsPro, aes(yintercept = Result))
# Figure_IsoField
# ggsave(Figure_IsoField, filename = file.path('Figures', 'Sensitivity_Sink&Length.png'),width = 14,height = 8, dpi = 1200)


# Figure_IsoSink <- ggplot(sumstatsIsos_Am,aes(x = Tournament_Size, y = Result, group = Hole_distance, color= Hole_distance))+
#   #  ggplot(sumstatsIsos_Am,aes(x = Tournament_Size, y = Result, group = Sink_Probability, color= Sink_Probability))+
#   #  geom_point()+
#   #  geom_errorbar(aes(x = Tournament_Size, ymin=Result-ci, ymax=Result+ci, color= Sink_Probability),
#   #                width=.5, color = "blue")+
#   #  geom_line()+
#   stat_smooth()+
#   geom_point()+
#   labs(color = "Field Length")+
#   facet_grid(cols= vars(Sink_Probability),scales = "free", space = "free")+
#   geom_hline(aes(yintercept = ProScore, color= Hole_distance))+
#   #  geom_hline(yintercept = ave(sumstatsPro$Result[20]))+
#   ggtitle("Sensitivity to Field Length & Sink Probability") +
#   theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
#         axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
#         strip.text.y = element_text(size = 14))+
#   xlab("Tournament Size") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Score")
# #  geom_hline(sumstatsPro, aes(yintercept = Result))
# Figure_IsoSink
# ggsave(Figure_IsoSink, filename = file.path('Figures', 'Sensitivity_Length.png'),width = 14,height = 8, dpi = 1200)


# ## Updated Verification Plot 
# Sink0.5 <- filter(sumstatsIsos_Am,Sink_Probability==0.5)
# Figure_IsoSink2 <- ggplot(Sink0.5,aes(x = Tournament_Size, y = Result, group = Hole_distance, color= Hole_distance))+
#   #  ggplot(sumstatsIsos_Am,aes(x = Tournament_Size, y = Result, group = Sink_Probability, color= Sink_Probability))+
#   #  geom_point()+
#   #  geom_errorbar(aes(x = Tournament_Size, ymin=Result-ci, ymax=Result+ci, color= Sink_Probability),
#   #                width=.5, color = "blue")+
#   #  geom_line()+
#   theme_bw()+
#   stat_smooth()+
#   geom_point()+
#   labs(color = "Field Length")+
#   #  facet_grid(cols= vars(Sink_Probability),scales = "free", space = "free")+
#   geom_hline(aes(yintercept = ProScore, color= Hole_distance))+
#   #  geom_hline(yintercept = ave(sumstatsPro$Result[20]))+
#   ggtitle("Performance Sensitivity to Field Length") +
#   theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
#         axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
#         strip.text.y = element_text(size = 14))+
#   xlab("Tournament Size") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Score")+
#   xlim(0,200) # set X limit
# 
# #  geom_hline(sumstatsPro, aes(yintercept = Result))
# Figure_IsoSink2
# ggsave(Figure_IsoSink2, filename = file.path('Figures', 'Sensitivity_Length.png'),width = 7,height = 6, dpi = 1200)
# 
# ### Normalized
# Figure_IsoSink_normalized <- ggplot(sumstatsIsos_Am,aes(x = Tournament_Size, y = Normalized, group = Hole_distance, color= Hole_distance))+
#   #  ggplot(sumstatsIsos_Am,aes(x = Tournament_Size, y = Result, group = Sink_Probability, color= Sink_Probability))+
#   #  geom_point()+
#   #  geom_errorbar(aes(x = Tournament_Size, ymin=Result-ci, ymax=Result+ci, color= Sink_Probability),
#   #                width=.5, color = "blue")+
#   #  geom_line()+
#   stat_smooth()+
#   geom_point()+
#   labs(color = "Field Length")+
#   facet_grid(cols= vars(Sink_Probability),scales = "free", space = "free")+
#   #  geom_hline(aes(yintercept = ProScore, color= Hole_distance))+
#   #  geom_hline(yintercept = ave(sumstatsPro$Result[20]))+
#   ggtitle("Sensitivity to Field Length & Sink Probability") +
#   theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
#         axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
#         strip.text.y = element_text(size = 14))+
#   xlab("Tournament Size") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Normalized Score w.r.t. Pro Baseline")+
#   xlim(50,200)+ # set X limit
#   ylim(-5,30) # set y limit
# 
# #  geom_hline(sumstatsPro, aes(yintercept = Result))
# Figure_IsoSink_normalized
# ggsave(Figure_IsoSink_normalized, filename = file.path('Figures', 'Sensitivity_Length_normalized.png'),width = 14,height = 8, dpi = 1200)
# 
# ## normalized 2 for Zoe
# 
# Figure_IsoSink_normalized2 <- ggplot(Sink0.5,aes(x = Tournament_Size, y = Normalized, group = Hole_distance, color= Hole_distance))+
#   #  ggplot(sumstatsIsos_Am,aes(x = Tournament_Size, y = Result, group = Sink_Probability, color= Sink_Probability))+
#   #  geom_point()+
#   #  geom_errorbar(aes(x = Tournament_Size, ymin=Result-ci, ymax=Result+ci, color= Sink_Probability),
#   #                width=.5, color = "blue")+
#   #  geom_line()+
#   theme_bw()+
#   stat_smooth()+
#   geom_point()+
#   labs(color = "Field Length")+
#   #  facet_grid(cols= vars(Sink_Probability),scales = "free", space = "free")+
#   #  geom_hline(aes(yintercept = ProScore, color= Hole_distance))+
#   #  geom_hline(yintercept = ave(sumstatsPro$Result[20]))+
#   ggtitle("Normalized Performance Sensitivity to Field Length") +
#   theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
#         axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
#         strip.text.y = element_text(size = 14))+
#   xlab("Tournament Size") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Normalized Score w.r.t. Pro Baseline")
# #  xlim(50,200)+ # set X limit
# #  ylim(-5,30) # set y limit
# 
# #  geom_hline(sumstatsPro, aes(yintercept = Result))
# Figure_IsoSink_normalized2
# ggsave(Figure_IsoSink_normalized2, filename = file.path('Figures', 'Sensitivity_Length_normalized.png'),width = 7,height = 6, dpi = 1200)

########################
# Figure 2 - Value of letting others join parts
#######################

#StrokesLP_DS <- filter(Strokes, Architecture == "LP"|Architecture == "DS")
#StrokesLP_DS <- filter(StrokesLP_DS, Assignment != "AA"&Assignment != "PP"&Assignment != "SS")
#StrokesDecomposed <- filter(Strokes, Architecture != "H") 
StrokesDecomposed <- filter(Strokes, Score != 0)  # use this line for fixing the plots
StrokesDecomposed$ScoreNormed <- 1- StrokesDecomposed$Score/mean
StrokesDecomposed$CostNormed <- 1- StrokesDecomposed$cost/mean_cost


#Here is an ugly for loop to insert average costs to fix the plot (it was missing cost for some boxes)
# Need to replace 50 with the number of Monte-Carlo Iterations
StrokesDecomposed["AveCost"]<-0
r <-  1000 #set to number of runs
for (k in seq(1,nrow(StrokesDecomposed),r)){
  C=0
  B=0
  
  for (i in k:(k+r-1)){
    
    B = B+StrokesDecomposed$cost[i]
  }
  C = B/r
  for (j in k:(k+r-1)){
    
    StrokesDecomposed$AveCost[j] <- C
  }
}
# here I am calculating expected number of strokes for each architecture because I want
# to add it on the facet grid. There is probably a shorter way to do this but whatever
StrokesDecomposed["AveScore"]<-0
StrokesDecomposed["Match"]<-0

StrokesDecomposed_LP <- filter(StrokesDecomposed, Architecture == "LP") 
StrokesDecomposed_DAP <- filter(StrokesDecomposed, Architecture == "DAP")
StrokesDecomposed_DS <- filter(StrokesDecomposed, Architecture == "DS")
StrokesDecomposed_H  <- filter(StrokesDecomposed, Architecture == "H")

StrokesDecomposed_LP <-  StrokesDecomposed_LP %>%                                      
  mutate(AveScore = mean(ScoreNormed))# This line separates the LP matrix and computes the expected score 

# Following marks out the mismatches - Long assigned to Amateur
StrokesDecomposed_LP <-  StrokesDecomposed_LP %>%
  mutate(Match = ifelse(Assignment == "PA"|Assignment == "SA","Precondition",ifelse(Assignment == "AP","Absorb",ifelse(Assignment == "SP","Isolate",0)))) #Mark the ones whe Amateurs only Putt, 
#no good specialist matching in this architecture (No D module)


StrokesDecomposed_DAP <-  StrokesDecomposed_DAP %>%                       
  mutate(AveScore = mean(ScoreNormed)) #This line separates the LP matrix and computes the expected score

# Following marks out the mismatches and good matches - Drive assigned to Amateur or Pro
StrokesDecomposed_DAP <-  StrokesDecomposed_DAP %>%                       
  mutate(Match = ifelse(Assignment == "SPP"|Assignment == "SAA"|Assignment == "SAS","Isolate",ifelse(Assignment == "SAP","Isolate+Absorb",
                                                                                                     ifelse(Assignment == "PPA"|Assignment == "PAS"|Assignment == "PAA","Precondition",ifelse(Assignment == "AAP"|Assignment == "PAP","Absorb",ifelse(Assignment=="SPA", "Isolate+Precondition",0))))))

StrokesDecomposed_DS <-  StrokesDecomposed_DS %>%     
  mutate(AveScore = mean(ScoreNormed)) #This line separates the LP matrix and computes the expected score

# Following marks out the mismatches and good matches for DS - Drive assigned to Amateur or Pro

StrokesDecomposed_DS <-  StrokesDecomposed_DS %>%     
  mutate(Match = ifelse(Assignment == "PA","Precondition",ifelse(Assignment == "SP"|Assignment == "SA","Isolate",
                                                                 ifelse(Assignment == "AP","Absorb",0))))  


StrokesDecomposed_H <-  StrokesDecomposed_H %>%                                      
  mutate(AveScore = mean(ScoreNormed))# Thi
StrokesDecomposed_H <-  StrokesDecomposed_H %>%     
  mutate(Match = 0)

StrokesDecomposed <- rbind(StrokesDecomposed_LP,StrokesDecomposed_DAP,StrokesDecomposed_DS,StrokesDecomposed_H) #merging back.

############################
## Change P to G for Rebut##
############################

levels(StrokesDecomposed$Architecture)[levels(StrokesDecomposed$Architecture)=="DAP"] <- "TFG"
levels(StrokesDecomposed$Architecture)[levels(StrokesDecomposed$Architecture)=="DS"] <- "TS"
levels(StrokesDecomposed$Architecture)[levels(StrokesDecomposed$Architecture)=="LP"] <- "LG"


Figure2a <- ggplot(StrokesDecomposed)+
  geom_hline(yintercept = 1-mean/mean)+
  #geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Assignment, y = ScoreNormed, color = AveCost))+
  scale_color_gradient(low = "blue", high = "red")+
  labs(color =  "Relative Cost")+
  #  scale_color_gradientn(colours = rainbow(5))+
  facet_grid(rows = vars(Architecture),scales = "free", space = "free")+
  geom_hline(data=StrokesDecomposed,aes(yintercept=AveScore), color="#339999", linetype="dotdash", size=1)+
  coord_flip()+
  ggtitle("Performance of Alternative Architectures") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14))+
  xlab("Solver Assignment") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Solution Performance")
Figure2a
ggsave(Figure2a, filename = file.path('Figures', 'Performance.png'),width = 6.75,height = 6, dpi = 600)

Figure2a_sort <- ggplot(StrokesDecomposed)+
  geom_hline(yintercept = 1-mean/mean)+
  #geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x =reorder(Assignment, ScoreNormed, FUN = median), y = ScoreNormed, color = AveCost))+
  scale_color_gradient(low = "blue", high = "red")+
  labs(color =  "Relative Cost")+
  #  scale_color_gradientn(colours = rainbow(5))+
  facet_grid(rows = vars(Architecture),scales = "free", space = "free")+
  geom_hline(data=StrokesDecomposed,aes(yintercept=AveScore), color="#339999", linetype="dotdash", size=1)+
  coord_flip()+
  ggtitle("Performance of Alternative Architectures") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14))+
  xlab("Solver Assignment") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Solution Performance")
Figure2a_sort
ggsave(Figure2a_sort, filename = file.path('Figures', 'Performance_Cost_color.png'),width = 6,height = 6, dpi = 1200)

################################################
## New sorted figure for performance and Cost ##
################################################
Figure_Rebuttal_Perf_sort <- ggplot(StrokesDecomposed)+
  geom_hline(yintercept = 1-mean/mean)+
  #geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x =reorder(Assignment, ScoreNormed, FUN = median), y = ScoreNormed))+
  facet_grid(rows = vars(Architecture),scales = "free", space = "free")+
#  geom_hline(data=StrokesDecomposed,aes(yintercept=AveScore), color="#339999", linetype="dotdash", size=1)+
  coord_flip()+
  ggtitle("Performance of Alternative Architectures") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14))+
  xlab("Solver Assignment") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Solution Performance")
Figure_Rebuttal_Perf_sort
ggsave(Figure_Rebuttal_Perf_sort, filename = file.path('Figures', 'Rebuttal_Perf.png'),width = 6,height = 6, dpi = 1200)


Figure_Rebuttal_Cost_sort <- ggplot(StrokesDecomposed)+
  geom_hline(yintercept = 1-mean/mean)+
  #geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x =reorder(Assignment, CostNormed, FUN = median), y = CostNormed))+
  facet_grid(rows = vars(Architecture),scales = "free", space = "free")+
  #  geom_hline(data=StrokesDecomposed,aes(yintercept=AveScore), color="#339999", linetype="dotdash", size=1)+
  coord_flip()+
  ggtitle("Performance of Alternative Architectures") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14))+
  xlab("Solver Assignment") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Solution Performance")
Figure_Rebuttal_Cost_sort
ggsave(Figure_Rebuttal_Cost_sort, filename = file.path('Figures', 'Rebuttal_Cost.png'),width = 6,height = 6, dpi = 1200)



Figure2b <- ggplot(filter(sumstatsDecomp, Architecture != "H"))+
  geom_point(aes(x = Score, y = cost, color = Architecture, size = Fraction))+
  geom_errorbarh(aes(xmin=Score-sd, xmax=Score+sd,y = cost),height=1)+
  scale_size_continuous(range = c(4, 8))+
  labs(size =  "Fraction of \nExpert Usage", color = "Architecture")+
  geom_hline(yintercept = sumstatsDecomp$cost[4])+
  geom_vline(xintercept = mean)+
  ggtitle("Cost-Benefit Comparison") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14))+
  xlab("Score of the Innovation Strategy") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Cost of the Innovation Strategy")
Figure2b
ggsave(Figure2b, filename = file.path('Figures', 'Cost-Benefit.png'),width = 6,height = 6,dpi = 1200)

StrokesDAP <- filter(Strokes, Architecture == "DAP")
StrokesDAP <- filter(StrokesDAP, Assignment != "AAA"&Assignment != "PPP"&Assignment != "SSS")
StrokesDAP$Score <- StrokesDAP$Score - mean

# Figure2c <- ggplot(StrokesDAP)+
#   theme_bw()+  
#   geom_hline(yintercept = 0)+
#   geom_hline(yintercept = meanP100)+
#   geom_boxplot(aes(x = Assignment, y = Score))+
#   facet_grid(cols = vars(Architecture),scales = "free")+
#   ggtitle("Performance of DAP Decompositions") +
#   theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
#         axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
#         strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
#   # ylab("Change (1-score/Pmean)")
#   ylab("Schedule Performance")  
# xlab("Assignment of Solver Types to Subproblems") +
#   ylab("Performance Change")
# Figure2c

####################### Plots for PNAS ########
Figure2d <- ggplot(StrokesDecomposed)+
  theme_bw()+
  geom_hline(yintercept = 1-mean/mean)+
  #geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Assignment, y = ScoreNormed, fill = Match))+
  labs(fill =  "Contractual Organization")+
  scale_fill_manual(values = c("#AAAAAA","#D30000", "#E69F00", "#00CED1"),
                    labels=c("Arbitrary Assignments","Proper Use of Amateurs","Ideal Use of all Solver Types","Speacialists Well-Matched"))+ #torquise 40E0D0 lightblue "#56B4E9" 
  facet_grid(rows = vars(Architecture),scales = "free", space = "free")+
  #  geom_hline(data=StrokesDecomposed,aes(yintercept=AveScore), color="#990000" ,linetype="dotdash", size=1)+
  coord_flip()+
  ggtitle("Performance of Alternative Contractual Strategies") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  guides(fill=guide_legend(nrow=2,byrow=TRUE))+
  xlab("Solver Assignment") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Schedule Performance")
Figure2d
ggsave(Figure2d, filename = file.path('Figures', 'Performance-Match.png'),width = 7,height = 7, dpi = 1200)

# Figure2dsort <- ggplot(StrokesDecomposed)+
#   theme_bw()+
#   geom_hline(yintercept = 1-mean/mean)+
#   #geom_hline(yintercept = meanP100)+
#   geom_boxplot(aes(x = reorder(Assignment, ScoreNormed, FUN = median), y = ScoreNormed, fill = Match))+
#   labs(fill =  "Contractual Organization")+
#   scale_fill_manual(values = c("#AAAAAA","#D30000", "#0072B2","#009E73","#E69F00","#CC79A7" ),
#                     labels=c("Arbitrary Assignments","Absorb - Pros to the Rescue","Isolate - Experts Well-Matched","Open - Proper Use of Amateurs","Precondition","biseyler"))+ #torquise 40E0D0 lightblue "#56B4E9" 
#   facet_grid(rows = vars(Architecture),scales = "free", space = "free")+
#   #  geom_hline(data=StrokesDecomposed,aes(yintercept=AveScore), color="#990000" ,linetype="dotdash", size=1)+
#   coord_flip()+
#   ggtitle("Performance of Alternative Contractual Strategies") +
#   theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
#         axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
#         strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
#   guides(fill=guide_legend(nrow=2,byrow=TRUE))+
#   xlab("Solver Assignment") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Schedule Performance")
# Figure2dsort
# ggsave(Figure2dsort, filename = file.path('Figures', 'Performance-Match_sorted.png'),width = 10,height = 10, dpi = 1200)
# ### Figure d fuzzy Good
# 
# Figure2dsort_fuzzy <- ggplot(filter(StrokesDecomposed, Score< 1.1*mean & cost<51.33*1.1))+
#   theme_bw()+
#   geom_hline(yintercept = 1-mean/mean)+
#   #geom_hline(yintercept = meanP100)+
#   geom_boxplot(aes(x = reorder(Assignment, ScoreNormed, FUN = median), y = ScoreNormed, fill = Match))+
#   labs(fill =  "Contractual Organization")+
#   scale_fill_manual(values = c("#AAAAAA","#D30000", "#0072B2","#009E73","#E69F00","#CC79A7" ),
#                     labels=c("Arbitrary Assignments","Absorb - Pros to the Rescue","Isolate - Experts Well-Matched","Isolate+Absorb","Isolate+Precondition","Precondition"))+ #torquise 40E0D0 lightblue "#56B4E9" 
#   facet_grid(rows = vars(Architecture),scales = "free", space = "free")+
#   #  geom_hline(data=StrokesDecomposed,aes(yintercept=AveScore), color="#990000" ,linetype="dotdash", size=1)+
#   coord_flip()+
#   ggtitle("Performance of Alternative Contractual Strategies") +
#   theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
#         axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
#         strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
#   guides(fill=guide_legend(nrow=2,byrow=TRUE))+
#   xlab("Solver Assignment") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Schedule Performance")
# Figure2dsort_fuzzy
# ggsave(Figure2dsort_fuzzy, filename = file.path('Figures', 'Performance-Match_fuzzycolor.png'),width = 6,height = 6, dpi = 1200)

### Figure 2d cost fuzzy

# Figure2dcost_fuzzy <- ggplot(filter(StrokesDecomposed, Score< 1.1*mean & cost<51.62222*1.1))+
#   theme_bw()+
#   #  geom_hline(yintercept = 51.62222)+
#   geom_hline(yintercept = 1-mean_cost/mean_cost)+
#   #geom_hline(yintercept = meanP100)+
#   geom_boxplot(aes(x = reorder(Assignment, ScoreNormed, FUN = median), y = CostNormed, fill = Match))+
#   labs(fill =  "Contractual Organization")+
#   scale_fill_manual(values = c("#AAAAAA","#D30000", "#0072B2","#009E73","#E69F00","#CC79A7" ),
#                     labels=c("Arbitrary Assignments","Absorb - Pros to the Rescue","Isolate - Experts Well-Matched","Isolate+Absorb","Isolate+Precondition","Precondition"))+ #torquise 40E0D0 lightblue "#56B4E9" 
#   facet_grid(rows = vars(Architecture),scales = "free", space = "free")+
#   #  geom_hline(data=StrokesDecomposed,aes(yintercept=AveScore), color="#990000" ,linetype="dotdash", size=1)+
#   coord_flip()+
#   ggtitle("Cost of Alternative Contractual Strategies") +
#   theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
#         axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
#         strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
#   guides(fill=guide_legend(nrow=2,byrow=TRUE))+
#   xlab("Solver Assignment") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Cost Performance")
# Figure2dcost_fuzzy
# ggsave(Figure2dcost_fuzzy, filename = file.path('Figures', 'Cost-Match_fuzzycolor.png'),width = 6,height = 6, dpi = 1200)
# ##

# Figure2e <- ggplot(sumstatsDecomp, Architecture != "H")+
#   theme_bw()+
#   geom_point(aes(x = Score, y = cost, color = Architecture, size = Fraction))+
#   #  geom_errorbarh(aes(xmin=Score-sd, xmax=Score+sd,y = cost),height=1)+
#   #  scale_size_continuous(range = c(4, 8))+
#   labs(size =  "Fraction of \nExpert Usage", color = "Architecture")+
#   #  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
#   geom_hline(yintercept = sumstatsDecomp$cost[4])+
#   geom_vline(xintercept = mean)+
#   ggtitle("Cost-Benefit Comparison") +
#   theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
#         axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
#         strip.text.y = element_text(size = 14))+
#   xlab("Score of the Innovation Strategy") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Cost of the Innovation Strategy")
# Figure2e
# ggsave(Figure2e, filename = file.path('Figures', 'Cost-Benefit.png'),width = 6,height = 6,dpi = 1200)

#### This is Figure 6a
Figure2efull <- ggplot(filter(sumstatsDecomp, Score != 0) )+
  theme_bw()+
  geom_point(aes(x = Score, y = cost, color = Architecture, size = Fraction))+
  #  geom_errorbarh(aes(xmin=Score-sd, xmax=Score+sd,y = cost),height=1)+
  #  scale_size_continuous(range = c(4, 8))+
  labs(color = "Architecture", size =  "Fraction of \nExpert Reliance")+
  #  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
  #  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
  geom_hline(yintercept = sumstatsDecomp$cost[4])+
  geom_vline(xintercept = mean)+
#  ggtitle("Innovation Outcomes") +
  ggtitle("Design Process Outcomes")+
    theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14))+
  xlab("Performance") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Cost")
#  xlim(NA,mean*1.2)+ # set X limit+
#  ylim(NA,1.2*sumstatsDecomp$cost[4]) # set y limit
Figure2efull
ggsave(Figure2efull, filename = file.path('Figures', 'Design_Process_Outcomes.png'),width = 6,height = 6,dpi = 1200)

## for Decomp Proposal ## we ended up not using this at all!
# Figure_Prop <- ggplot(filter(sumstatsDecomp, Score != 0) )+
#   theme_bw()+
#   geom_point(aes(x = Score, y = cost, color = Architecture, size = Fraction))+
#   geom_errorbarh(aes(xmin=Score-sd, xmax=Score+sd,y = cost),height=1.5)+
# #  geom_errorbar(aes(ymin=cost-cost_sd, ymax=cost+cost_sd,x = Score),height=1)+
#   #  scale_size_continuous(range = c(4, 8))+
#   labs(size =  "Fraction of \nExpert Usage", color = "Architecture")+
#   #  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
#   #  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
#   geom_hline(yintercept = sumstatsDecomp$cost[4])+
#   geom_vline(xintercept = mean)+
#   ggtitle("Decomposition + Solver Assignment Outcomes") +
#   theme(plot.title = element_text(size=12,face="bold", hjust = 1),axis.text=element_text(size=12),
#         axis.title.x = element_text(size=12,face="bold"),axis.title.y = element_text(size=12,face="bold"),
#         strip.text.y = element_text(size = 12))+
#   xlab("Performance") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Cost")
# #  xlim(NA,mean*1.2)+ # set X limit+
# #  ylim(NA,1.2*sumstatsDecomp$cost[4]) # set y limit
# Figure_Prop
# ggsave(Figure_Prop, filename = file.path('Figures', 'Proposal.png'),width = 6,height = 6,dpi = 1200)


# Figure2efilt <- ggplot(filter(sumstatsDecomp, (Score != 0 & (Score< 1.2*mean | cost<costmean*1.2))))+
#   theme_bw()+
#   geom_point(aes(x = Score, y = cost, color = Architecture, size = Fraction))+
#   #  geom_errorbarh(aes(xmin=Score-sd, xmax=Score+sd,y = cost),height=1)+
#   #  scale_size_continuous(range = c(4, 8))+
#   labs(size =  "Fraction of \nExpert Usage", color = "Architecture")+
#   #  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
#   #  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
#   geom_hline(yintercept = sumstatsDecomp$cost[4])+
#   geom_vline(xintercept = mean)+
#   ggtitle("Innovation Outcomes") +
#   theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
#         axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
#         strip.text.y = element_text(size = 14))+
#   xlab("Performance") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Cost")
# #  xlim(NA,mean*1.2)+ # set X limit+
# #  ylim(NA,1.2*sumstatsDecomp$cost[4]) # set y limit
# Figure2efilt
# ggsave(Figure2efilt, filename = file.path('Figures', 'InnovationOutcomes_filt2.png'),width = 6,height = 6,dpi = 1200)


#### Figure 2e with Combinations printed!

Figure2e_fuz <- ggplot(filter(sumstatsDecomp, Score != 0) )+
  theme_bw()+
  geom_point(aes(x = Score, y = cost, color = Architecture, size = Fraction))+
  #  geom_errorbarh(aes(xmin=Score-sd, xmax=Score+sd,y = cost),height=1)+
  #  scale_size_continuous(range = c(4, 8))+
  labs(size =  "Fraction of \nExpert Usage", color = "Architecture")+
  #  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
  geom_hline(yintercept = sumstatsDecomp$cost[4])+
  geom_vline(xintercept = mean)+
  ggtitle("Innovation Outcomes") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14))+
  xlab("Performance") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Cost")
  #  geom_rect(aes(xmin=25,xmax=Inf, ymin=1.1*sumstatsDecomp$cost[4], ymax=Inf),alpha=0.01)+
  #  geom_rect(aes(xmin=mean*1.1,xmax=Inf, ymin=8,  ymax=1.1*sumstatsDecomp$cost[4]), alpha=0.01)
#  geom_rect(aes(xmin=32.5,xmax=mean*1.1, ymin=25,  ymax=1.1*sumstatsDecomp$cost[4]), size=1, color="gold", fill= NA)
#  geom_rect(aes(xmin=mean*1.2, xmax=Inf))
#  xlim(NA,mean*1.1)+ # set X limit+
#  ylim(25,1.1*sumstatsDecomp$cost[4]) # set y limit
Figure2e_fuz
ggsave(Figure2e_fuz, filename = file.path('Figures', 'Cost-Benefit_sens_cut.png'),width = 6,height = 6,dpi = 1200)


Figure2e_fuzfilt <- ggplot(filter(sumstatsDecomp,Score != 0&Fraction<0.75&Score< 1.2*mean & cost<mean_cost*1.2))+
  theme_bw()+
  geom_point(aes(x = Score, y = cost, color = Architecture, size = Fraction))+
  #  geom_errorbarh(aes(xmin=Score-sd, xmax=Score+sd,y = cost),height=1)+
  #  scale_size_continuous(range = c(4, 8))+
  labs(size =  "Fraction of \nExpert Usage", color = "Architecture")+
  #  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
  geom_hline(yintercept = sumstatsDecomp$cost[4])+
  geom_vline(xintercept = mean)+
  ggtitle("Fuzzy Dominant Solutions") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14))+
  xlab("Performance") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Cost")
#  geom_rect(aes(xmin=25,xmax=Inf, ymin=1.1*sumstatsDecomp$cost[4], ymax=Inf),alpha=0.01)+
#  geom_rect(aes(xmin=mean*1.1,xmax=Inf, ymin=8,  ymax=1.1*sumstatsDecomp$cost[4]), alpha=0.01)
#  geom_rect(aes(xmin=30,xmax=mean*1.1, ymin=25,  ymax=1.1*sumstatsDecomp$cost[4]), size=1, color="gold", fill= NA)
#  geom_rect(aes(xmin=mean*1.2, xmax=Inf))
#  xlim(NA,mean*1.1)+ # set X limit+
#  ylim(25,1.1*sumstatsDecomp$cost[4]) # set y limit
Figure2e_fuzfilt
ggsave(Figure2e_fuzfilt, filename = file.path('Figures', 'Cost-Benefit_sens_filt.png'),width = 6,height = 6,dpi = 1200)
###################################################
############# New Figure For Strategies###########
###################################################

##### Now we can finally (!) Plot ######

# Figure_Sp_Assignment <- ggplot(filter(la2,Percent_Improv != 0))+
# #  geom_hline(yintercept = 1-mean/mean)+
#   #geom_hline(yintercept = meanP100)+
#   theme_bw()+
#   geom_bar(aes(x = Reference_Label, y = Percent_Improv, fill = Delta_Label),stat = "identity", position="dodge")+
#   #geom_boxplot(aes(x = Reference_Label, y = Percent_Improv, fill = Delta_Label))+
# #  scale_color_gradient(low = "blue", high = "red")+
#   #labs(color =  "Replaced Solver Assignment")+
#   labs(fill = "Solver Replacement")+
#   scale_y_continuous(labels = scales::percent)+
#     #  scale_color_gradientn(colours = rainbow(5))+
#   facet_grid(cols = vars(Architecture),scales = "free", space = "free")+
# #  facet_grid(rows = vars(Architecture),scales = "free", space = "free")+
#   
# #  scale_y_continuous(labels = scales::percent)+
#   #  geom_hline(data=StrokesDecomposed,aes(yintercept=AveScore), color="#339999", linetype="dotdash", size=1)+
# #  coord_flip()+
#   ggtitle("Impact of Specialist Drive Assignment") +
#   theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=14),
#         axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
#         strip.text.y = element_text(size = 14),strip.text.x = element_text(size = 14),legend.position="bottom",legend.title=element_text(size=12),legend.text=element_text(size=12))+
#   xlab("Solver Assignment") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Percent Improvement in Performance")
# Figure_Sp_Assignment
# ggsave(Figure_Sp_Assignment, filename = file.path('Figures', 'SP_assignment.png'),width = 8,height = 8, dpi = 1200)

sokuk_0 <- filter(la2,Delta_Label == "Pro")
sokuk <- select(sokuk_0,c(1,20,29,30))
#sokuk2 <- melt(sokuk, id.vars=c('Architecture', 'Reference_Label',),var='color')
sokuk2 <- gather(sokuk, Change, value, -Architecture, -Reference_Label)

sokuk2[sokuk2 == "Percent_Improv"] <- "Performance"
sokuk2[sokuk2 == "Percent_Improv_Cost"] <- "Cost"

Figure_Sp_Assignment2 <- ggplot(sokuk2)+
  #  geom_hline(yintercept = 1-mean/mean)+
  #geom_hline(yintercept = meanP100)+
  theme_bw()+
  geom_bar(aes(x = reorder(Reference_Label, -value), y =value, fill= Change),stat = "identity", position= position_dodge(width = 0.0))+
#  geom_bar(aes(x = Reference_Label, y =Percent_Improv_Cost),stat = "identity")+
  #geom_boxplot(aes(x = Reference_Label, y = Percent_Improv, fill = Delta_Label))+
  #  scale_color_gradient(low = "blue", high = "red")+
  #labs(color =  "Replaced Solver Assignment")+
  labs(fill = "Outcome Measure")+
  scale_y_continuous(labels = scales::percent)+
  #  scale_color_gradientn(colours = rainbow(5))+
  facet_grid(cols = vars(Architecture),scales = "free", space = "free")+
  #  facet_grid(rows = vars(Architecture),scales = "free", space = "free")+
  
  #  scale_y_continuous(labels = scales::percent)+
  #  geom_hline(data=StrokesDecomposed,aes(yintercept=AveScore), color="#339999", linetype="dotdash", size=1)+
  #  coord_flip()+
  ggtitle("Impact of Replacing Pros with a Specialist on Tee") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),strip.text.x = element_text(size = 14),legend.position="bottom",legend.title=element_text(size=12),legend.text=element_text(size=12))+
  xlab("Solver Assignment") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Percent Change")
Figure_Sp_Assignment2
ggsave(Figure_Sp_Assignment2, filename = file.path('Figures', 'SP_assignment2.png'),width = 8,height = 8, dpi = 1200)


#### 

Am_Impact_dummy <- filter(la3,Delta_Green_Label == "Pro")
Am_Impact_Green <- select(Am_Impact_dummy,c(1,23,29,30))
#sokuk2 <- melt(sokuk, id.vars=c('Architecture', 'Reference_Label',),var='color')
Am_Impact_Green_long <- gather(Am_Impact_Green, Change, value, -Architecture, -Reference_Green_Label)

Am_Impact_Green_long[Am_Impact_Green_long == "Percent_Green_Improv"] <- "Performance"
Am_Impact_Green_long[Am_Impact_Green_long == "Percent_Green_Improv_Fraction"] <- "Expert Reliance"

cols <- c("Performance" = "#00BFC4", "Expert Reliance" = "#7CAE00")

#Am_Impact_Green_long <- arrange(Am_Impact_Green_long,value)

Figure_Am_Assignment <- ggplot(filter(Am_Impact_Green_long))+
#  geom_hline(yintercept = 1-mean/mean)+
#geom_hline(yintercept = meanP100)+
  theme_bw()+
  geom_bar(aes(x = reorder(Reference_Green_Label, -value), y = value, fill = Change),stat = "identity", position= position_dodge(width = 0.50))+
  #geom_boxplot(aes(x = Reference_Label, y = Percent_Improv, fill = Delta_Label))+
  #  scale_color_gradient(low = "blue", high = "red")+
  #labs(color =  "Replaced Solver Assignment")+
#                      scale_color_manual(values = c("#AAAAAA","#D30000", "#E69F00", "#00CED1")
  labs(fill = "Outcome Measure")+
  scale_y_continuous(labels = scales::percent)+
  #  scale_color_gradientn(colours = rainbow(5))+
  facet_grid(cols = vars(Architecture),scales = "free", space = "free")+
  #  facet_grid(rows = vars(Architecture),scales = "free", space = "free")+
  
  #  scale_y_continuous(labels = scales::percent)+
  #  geom_hline(data=StrokesDecomposed,aes(yintercept=AveScore), color="#339999", linetype="dotdash", size=1)+
  #  coord_flip()+
  scale_fill_manual(values = cols) +
  ggtitle("Impact of Amateur Green Assignment") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),strip.text.x = element_text(size = 14),legend.position="bottom",legend.title=element_text(size=12),legend.text=element_text(size=12))+
  xlab("Solver Assignment") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Percent Improvement in Performance")
Figure_Am_Assignment
ggsave(Figure_Am_Assignment, filename = file.path('Figures', 'Am_assignment.png'),width = 8,height = 8, dpi = 1200)


# Figure_Am_Assignment <- ggplot(filter(la3,Percent_Green_Improv != 0))+
#   #  geom_hline(yintercept = 1-mean/mean)+
#   #geom_hline(yintercept = meanP100)+
#   theme_bw()+
#   geom_bar(aes(x = Reference_Green_Label, y = Percent_Green_Improv, fill = Delta_Green_Label),stat = "identity", position="dodge")+
#   #geom_boxplot(aes(x = Reference_Label, y = Percent_Improv, fill = Delta_Label))+
#   #  scale_color_gradient(low = "blue", high = "red")+
#   #labs(color =  "Replaced Solver Assignment")+
#   labs(fill = "Solver Replacement")+
#   scale_y_continuous(labels = scales::percent)+
#   #  scale_color_gradientn(colours = rainbow(5))+
#   facet_grid(cols = vars(Architecture),scales = "free", space = "free")+
#   #  facet_grid(rows = vars(Architecture),scales = "free", space = "free")+
#   
#   #  scale_y_continuous(labels = scales::percent)+
#   #  geom_hline(data=StrokesDecomposed,aes(yintercept=AveScore), color="#339999", linetype="dotdash", size=1)+
#   #  coord_flip()+
#   ggtitle("Impact of Amateur Green Assignment") +
#   theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=14),
#         axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
#         strip.text.y = element_text(size = 14),strip.text.x = element_text(size = 14),legend.position="bottom",legend.title=element_text(size=12),legend.text=element_text(size=12))+
#   xlab("Solver Assignment") + 
#   # ylab("Change (1-score/Pmean)")
#   ylab("Percent Improvement in Performance")
# Figure_Am_Assignment
# ggsave(Figure_Am_Assignment, filename = file.path('Figures', 'Am_assignment.png'),width = 8,height = 8, dpi = 1200)

########################
#### Sensitivity ####
########################
### Color the sumstats decomp for sensitivity figure

sumstatsDecomp["Dominant"]<-0
sumstatsDecomp <-  sumstatsDecomp %>%
  mutate(Dominant = ifelse(((Architecture == "TS"& Assignment == "SA")|((Architecture == "TFG"& (Assignment == "SAA"|Assignment == "SAP")))),"Dom",
                           ifelse(((Architecture == "TS"& Assignment == "SP"| Assignment == "PA")|((Architecture == "TFG"& (Assignment == "SPA"|Assignment == "SPP"|Assignment == "SAS")))),"Fuzzy","New")))       



#### Sensitivity Baseline Plot (Predecessor of Figure 7)
Figure2e_WideFuz <- ggplot(filter(sumstatsDecomp,Score != 0&((Score<mean | cost<Bench_Cost) & (Fraction<=0.75&cost<1.2*Bench_Cost&Score<1.2*mean))))+
  theme_bw()+
  geom_point(aes(x = Score, y = cost, color = Dominant, shape = Architecture, size = 2))+
  #  geom_errorbarh(aes(xmin=Score-sd, xmax=Score+sd,y = cost),height=1)+
  #  scale_size_continuous(range = c(4, 8))+
    labs(color =  "Dominance in the \nBaseline Case", shape = "Architecture")+
  #  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
  geom_hline(yintercept = mean)+
  geom_vline(xintercept = Bench_Cost)+
  ggtitle("Double Coordination Costs") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14),legend.text=element_text(size=12), legend.title =element_text(size=12,face="bold"),legend.position = c(0.75, 0.35))+
  guides(size = FALSE)+
  #, legend.position = c(0.8, 0.4)
  #legend.position = c(0.8, 0.2)
  #,legend.position = "none"
  #legend.text=element_text(size=12), legend.title =element_text(size=12,face="bold")
  xlab("Performance") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Cost")+
  #  geom_rect(aes(xmin=25,xmax=Inf, ymin=1.1*sumstatsDecomp$cost[4], ymax=Inf),alpha=0.01)+
  #  geom_rect(aes(xmin=mean*1.1,xmax=Inf, ymin=8,  ymax=1.1*sumstatsDecomp$cost[4]), alpha=0.01)
  #  geom_rect(aes(xmin=30,xmax=mean*1.1, ymin=25,  ymax=1.1*sumstatsDecomp$cost[4]), size=1, color="gold", fill= NA)
  #  geom_rect(aes(xmin=mean*1.2, xmax=Inf))
  xlim(33,55)+ # set X limit+
  ylim(30,60) # set y limit
Figure2e_WideFuz
ggsave(Figure2e_WideFuz, filename = file.path('Figures', 'Wide-Fuzzy Sensitivity_DC.png'),width = 3,height = 3,dpi = 1200)



Figure2e_WideFuz_20 <- ggplot(filter(sumstatsDecomp,Score != 0&((Score<mean | cost<Bench_Cost) & (Fraction<=0.75&cost<1.2*Bench_Cost&Score<1.2*mean))))+
  theme_bw()+
  geom_point(aes(x = Score, y = cost, color = Dominant, shape = Architecture, size = 2))+
  #  geom_errorbarh(aes(xmin=Score-sd, xmax=Score+sd,y = cost),height=1)+
  #  scale_size_continuous(range = c(4, 8))+
    labs(color =  "Dominance in the \nBaseline Case", shape = "Architecture")+
  #  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
  geom_hline(yintercept = 52.17889)+
  geom_vline(xintercept = 46.961)+
  ggtitle("Double Coordination Costs") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14),legend.text=element_text(size=12), legend.title =element_text(size=12,face="bold"))+
  guides(size = FALSE)+
  #,legend.position = "none"
  # ,legend.text=element_text(size=12),legend.title =element_text(size=12,face="bold")
  xlab("Performance") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Cost")+
  #  geom_rect(aes(xmin=25,xmax=Inf, ymin=1.1*sumstatsDecomp$cost[4], ymax=Inf),alpha=0.01)+
  #  geom_rect(aes(xmin=mean*1.1,xmax=Inf, ymin=8,  ymax=1.1*sumstatsDecomp$cost[4]), alpha=0.01)
  #  geom_rect(aes(xmin=30,xmax=mean*1.1, ymin=25,  ymax=1.1*sumstatsDecomp$cost[4]), size=1, color="gold", fill= NA)
  #  geom_rect(aes(xmin=mean*1.2, xmax=Inf))
  xlim(33,55)+ # set X limit+
  ylim(30,65) # set y limit
Figure2e_WideFuz_20
ggsave(Figure2e_WideFuz_20, filename = file.path('Figures', 'Wide-Fuzzy Sensitivity_DC20.png'),width = 3,height = 3,dpi = 1200)





### Innovation impact bar plot 
sumBar <- filter(filter(sumstatsDecomp,Score != 0))
sumBar["Schedule"]<-0
sumBar["Schedule_Count"]<-0
sumBar["Budget"]<-0
sumBar["Budget_Count"]<-0
Bench_Cost<-sumBar$cost[2]
sumBar["ReduceExpert"]<-0
sumBar["ReduceExpert_Count"]<-0
sumBar["Dominant"]<-0
sumBar["Dominant_Count"]<-0
sumBar["Counter"]<-1

## Check which alternatives are better, fuzzy, or worse
sumBar<-  sumBar %>%
  mutate(Schedule = ifelse((Score<mean),"Yes",ifelse((Score>1.2*mean),"No","Fuzzy")))%>%
  mutate(Budget = ifelse((cost<Bench_Cost),"Yes",ifelse((cost>1.2*Bench_Cost),"No","Fuzzy")))%>%
  mutate(ReduceExpert = ifelse((Fraction<=0.75 & cost<1.2*Bench_Cost & Score<1.2*mean),"Yes",ifelse((Fraction==1),"No","Minor")))%>%
  mutate(Dominant = ifelse((Fraction<0.75 & cost<Bench_Cost & Score<mean),"Yes",ifelse((Score<mean | cost<Bench_Cost) & (Fraction<=0.75&cost<1.2*Bench_Cost&Score<1.2*mean),"Fuzzy","No")))


# ## Check which alternatives are better, fuzzy, or worse
# sumBar<-  sumBar %>%
#   mutate(Schedule = ifelse((Score<mean),"Yes",ifelse((Score>1.11*mean),"No","Fuzzy")))%>%
#   mutate(Budget = ifelse((cost<Bench_Cost),"Yes",ifelse((cost>1.11*Bench_Cost),"No","Fuzzy")))%>%
#   mutate(ReduceExpert = ifelse((Fraction<=0.75 & cost<1.2*Bench_Cost & Score<1.2*mean),"Yes",ifelse((Fraction==1),"No","Minor")))%>%
#   mutate(Dominant = ifelse((Fraction<0.75 & cost<Bench_Cost & Score<mean),"Yes",ifelse((Score<mean | cost<Bench_Cost) & (Fraction<=0.75&cost<1.11*Bench_Cost&Score<1.11*mean),"Fuzzy","No")))
# ## the old version of dominant fuzzy


## the old version of dominant fuzzy
#mutate(Dominant = ifelse((Fraction<0.75 & cost<Bench_Cost & Score<mean),"Yes",ifelse((Score<mean | cost<Bench_Cost | (Fraction<=0.75&cost<1.2*Bench_Cost&Score<1.2*mean)) &
#(Score<=1.1*mean & cost<=1.1*Bench_Cost & Fraction<0.85),"Fuzzy","No")))

## Extracting Yes-No-Fuzzy Counts for each facet
## Schedule
Schedule_H_No <-nrow(filter(sumBar,Architecture == "H" & Schedule=="No"))
Schedule_H_Fuzzy <- nrow(filter(sumBar,Architecture == "H" & Schedule=="Fuzzy"))
Schedule_H_Yes <- nrow(filter(sumBar,Architecture == "H" & Schedule=="Yes"))
Schedule_LP_No <-nrow(filter(sumBar,Architecture == "LG" & Schedule=="No"))
Schedule_LP_Fuzzy <- nrow(filter(sumBar,Architecture == "LG" & Schedule=="Fuzzy"))
Schedule_LP_Yes <- nrow(filter(sumBar,Architecture == "LG" & Schedule=="Yes"))
Schedule_DAP_No <-nrow(filter(sumBar,Architecture == "TFG" & Schedule=="No"))
Schedule_DAP_Fuzzy <- nrow(filter(sumBar,Architecture == "TFG" & Schedule=="Fuzzy"))
Schedule_DAP_Yes <- nrow(filter(sumBar,Architecture == "TFG" & Schedule=="Yes"))
Schedule_DS_No <-nrow(filter(sumBar,Architecture == "TS" & Schedule=="No"))
Schedule_DS_Fuzzy <- nrow(filter(sumBar,Architecture == "TS" & Schedule=="Fuzzy"))
Schedule_DS_Yes <- nrow(filter(sumBar,Architecture == "TS" & Schedule=="Yes"))
## Writing in the continous values for Schedule
sumBar<-  sumBar %>%
  mutate(Schedule_Count = case_when((Architecture == "H" & Schedule=="No")~Schedule_H_No,(Architecture == "H" & Schedule=="Fuzzy")~Schedule_H_Fuzzy,
                                    ((Architecture == "LG" & Schedule=="No")~ Schedule_LP_No),((Architecture == "LG" & Schedule=="Fuzzy")~Schedule_LP_Fuzzy),((Architecture == "LG" & Schedule=="Yes")~ Schedule_LP_Yes),
                                    ((Architecture == "TFG" & Schedule=="No")~ Schedule_DAP_No),((Architecture == "TFG" & Schedule=="Fuzzy")~ Schedule_DAP_Fuzzy),((Architecture == "TFG" & Schedule=="Yes")~ Schedule_DAP_Yes),
                                    ((Architecture == "TS" & Schedule=="No")~ Schedule_DS_No),((Architecture == "TS" & Schedule=="Fuzzy")~ Schedule_DS_Fuzzy),((Architecture == "TS" & Schedule=="Yes")~ Schedule_DS_Yes)))
#                                  ((Architecture == "LP" & Schedule=="No")~2
#                                  ((Architecture == "DAP" & (Assignment == "SAA"|Assignment == "SAS"|Assignment == "SPP"|Assignment == "SPS"|
#                                                               Assignment == "SSP"|Assignment == "SSS"))|(Architecture == "DS" & (Assignment == "SP"|Assignment == "SS")))~"Sp",
#                                  ((Architecture=="DAP" & (Assignment == "SAP"|Assignment == "SPA"))|(Architecture == "DS" & Assignment == "SA"))~"Ideal"))
##count Cost
Budget_H_No <-nrow(filter(sumBar,Architecture == "H" & Budget=="No"))
Budget_H_Fuzzy <- nrow(filter(sumBar,Architecture == "H" & Budget=="Fuzzy"))
Budget_H_Yes <- nrow(filter(sumBar,Architecture == "H" & Budget=="Yes"))
Budget_LP_No <-nrow(filter(sumBar,Architecture == "LG" & Budget=="No"))
Budget_LP_Fuzzy <- nrow(filter(sumBar,Architecture == "LG" & Budget=="Fuzzy"))
Budget_LP_Yes <- nrow(filter(sumBar,Architecture == "LG" & Budget=="Yes"))
Budget_DAP_No <-nrow(filter(sumBar,Architecture == "TFG" & Budget=="No"))
Budget_DAP_Fuzzy <- nrow(filter(sumBar,Architecture == "TFG" & Budget=="Fuzzy"))
Budget_DAP_Yes <- nrow(filter(sumBar,Architecture == "TFG" & Budget=="Yes"))
Budget_DS_No <-nrow(filter(sumBar,Architecture == "TS" & Budget=="No"))
Budget_DS_Fuzzy <- nrow(filter(sumBar,Architecture == "TS" & Budget=="Fuzzy"))
Budget_DS_Yes <- nrow(filter(sumBar,Architecture == "TS" & Budget=="Yes"))
## Writing in the continous values for Cost
sumBar<-  sumBar %>%
  mutate(Budget_Count = case_when((Architecture == "H" & Budget=="No")~Budget_H_No,(Architecture == "H" & Budget=="Fuzzy")~Budget_H_Fuzzy,(Architecture == "H" & Budget=="Yes")~Budget_H_Yes,
                                  ((Architecture == "LG" & Budget=="No")~ Budget_LP_No),((Architecture == "LG" & Budget=="Fuzzy")~Budget_LP_Fuzzy),((Architecture == "LG" & Budget=="Yes")~ Budget_LP_Yes),
                                  ((Architecture == "TFG" & Budget=="No")~ Budget_DAP_No),((Architecture == "TFG" & Budget=="Fuzzy")~ Budget_DAP_Fuzzy),((Architecture == "TFG" & Budget=="Yes")~ Budget_DAP_Yes),
                                  ((Architecture == "TS" & Budget=="No")~ Budget_DS_No),((Architecture == "TS" & Budget=="Fuzzy")~ Budget_DS_Fuzzy),((Architecture == "TS" & Budget=="Yes")~ Budget_DS_Yes)))
## count Expert Fraction
ReduceExpert_H_No <-nrow(filter(sumBar,Architecture == "H" & ReduceExpert=="No"))
ReduceExpert_H_Fuzzy <- nrow(filter(sumBar,Architecture == "H" & ReduceExpert=="Minor"))
ReduceExpert_H_Yes <- nrow(filter(sumBar,Architecture == "H" & ReduceExpert=="Yes"))
ReduceExpert_LP_No <-nrow(filter(sumBar,Architecture == "LG" & ReduceExpert=="No"))
ReduceExpert_LP_Fuzzy <- nrow(filter(sumBar,Architecture == "LG" & ReduceExpert=="Minor"))
ReduceExpert_LP_Yes <- nrow(filter(sumBar,Architecture == "LG" & ReduceExpert=="Yes"))
ReduceExpert_DAP_No <-nrow(filter(sumBar,Architecture == "TFG" & ReduceExpert=="No"))
ReduceExpert_DAP_Fuzzy <- nrow(filter(sumBar,Architecture == "TFG" & ReduceExpert=="Minor"))
ReduceExpert_DAP_Yes <- nrow(filter(sumBar,Architecture == "TFG" & ReduceExpert=="Yes"))
ReduceExpert_DS_No <-nrow(filter(sumBar,Architecture == "TS" & ReduceExpert=="No"))
ReduceExpert_DS_Fuzzy <- nrow(filter(sumBar,Architecture == "TS" & ReduceExpert=="Minor"))
ReduceExpert_DS_Yes <- nrow(filter(sumBar,Architecture == "TS" & ReduceExpert=="Yes"))
#write in expert fraction
sumBar<-  sumBar %>%
  mutate(ReduceExpert_Count = case_when((Architecture == "H" & ReduceExpert=="No")~ReduceExpert_H_No,(Architecture == "H" & ReduceExpert=="Minor")~ReduceExpert_H_Fuzzy,(Architecture == "H" & ReduceExpert=="Yes")~ReduceExpert_H_Yes,
                                        ((Architecture == "LG" & ReduceExpert=="No")~ ReduceExpert_LP_No),((Architecture == "LG" & ReduceExpert=="Minor")~ReduceExpert_LP_Fuzzy),((Architecture == "LG" & ReduceExpert=="Yes")~ ReduceExpert_LP_Yes),
                                        ((Architecture == "TFG" & ReduceExpert=="No")~ ReduceExpert_DAP_No),((Architecture == "TFG" & ReduceExpert=="Minor")~ ReduceExpert_DAP_Fuzzy),((Architecture == "TFG" & ReduceExpert=="Yes")~ ReduceExpert_DAP_Yes),
                                        ((Architecture == "TS" & ReduceExpert=="No")~ ReduceExpert_DS_No),((Architecture == "TS" & ReduceExpert=="Minor")~ ReduceExpert_DS_Fuzzy),((Architecture == "TS" & ReduceExpert=="Yes")~ ReduceExpert_DS_Yes)))
## Count dominants
Dominant_H_No <-nrow(filter(sumBar,Architecture == "H" & Dominant=="No"))
Dominant_H_Fuzzy <- nrow(filter(sumBar,Architecture == "H" & Dominant=="Fuzzy"))
Dominant_H_Yes <- nrow(filter(sumBar,Architecture == "H" & Dominant=="Yes"))
Dominant_LP_No <-nrow(filter(sumBar,Architecture == "LG" & Dominant=="No"))
Dominant_LP_Fuzzy <- nrow(filter(sumBar,Architecture == "LG" & Dominant=="Fuzzy"))
Dominant_LP_Yes <- nrow(filter(sumBar,Architecture == "LG" & Dominant=="Yes"))
Dominant_DAP_No <-nrow(filter(sumBar,Architecture == "TFG" & Dominant=="No"))
Dominant_DAP_Fuzzy <- nrow(filter(sumBar,Architecture == "TFG" & Dominant=="Fuzzy"))
Dominant_DAP_Yes <- nrow(filter(sumBar,Architecture == "TFG" & Dominant=="Yes"))
Dominant_DS_No <-nrow(filter(sumBar,Architecture == "TS" & Dominant=="No"))
Dominant_DS_Fuzzy <- nrow(filter(sumBar,Architecture == "TS" & Dominant=="Fuzzy"))
Dominant_DS_Yes <- nrow(filter(sumBar,Architecture == "TS" & Dominant=="Yes"))
## Writing in the continous values for Dominance
sumBar<-  sumBar %>%
  mutate(Dominant_Count = case_when((Architecture == "H" & Dominant=="No")~Dominant_H_No,(Architecture == "H" & Dominant=="Fuzzy")~Dominant_H_Fuzzy,(Architecture == "H" & Dominant=="Yes")~Dominant_H_Yes,
                                    ((Architecture == "LG" & Dominant=="No")~ Dominant_LP_No),((Architecture == "LG" & Dominant=="Fuzzy")~Dominant_LP_Fuzzy),((Architecture == "LG" & Dominant=="Yes")~ Dominant_LP_Yes),
                                    ((Architecture == "TFG" & Dominant=="No")~ Dominant_DAP_No),((Architecture == "TFG" & Dominant=="Fuzzy")~ Dominant_DAP_Fuzzy),((Architecture == "TFG" & Dominant=="Yes")~ Dominant_DAP_Yes),
                                    ((Architecture == "TS" & Dominant=="No")~ Dominant_DS_No),((Architecture == "TS" & Dominant=="Fuzzy")~ Dominant_DS_Fuzzy),((Architecture == "TS" & Dominant=="Yes")~ Dominant_DS_Yes)))

sumBar$Schedule <- factor(sumBar$Schedule, level = c("Yes","Fuzzy","No"))
names(sumBar)[17] <- "Performance"
## Bar Plot for Impact on Schedule
Figure_Impact_Performance <- ggplot(sumBar, aes(x=Architecture, y=Counter, fill=Schedule))+
  theme_bw()+
  geom_bar(stat = "identity",position = "fill")+
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=16),
        axis.title.x = element_text(size=16,face="bold"),axis.title.y = element_text(size=16,face="bold"),
        strip.text.y = element_text(size = 16), legend.title=element_text(size=18,face="bold"), 
        legend.text=element_text(size=18))+
  xlab("Architecture") + 
  scale_y_continuous(labels = scales::percent)+
  # ylab("Change (1-score/Pmean)")
  ylab("Better Performance")+
  labs(fill = "Performance\nImprovement")
Figure_Impact_Performance
ggsave(Figure_Impact_Performance, filename = file.path('Figures', 'Impact_Schedule.png'),width = 6,height = 5,dpi = 1200)


## Bar Plot for Impact on Cost
sumBar$Budget <- factor(sumBar$Budget, level = c("Yes","Fuzzy","No"))

Figure_Impact_Budget <- ggplot(sumBar, aes(x=Architecture, y=Counter, fill=Budget))+
  theme_bw()+
  geom_bar(stat = "identity",position = "fill")+
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=16),
        axis.title.x = element_text(size=16,face="bold"),axis.title.y = element_text(size=16,face="bold"),
        strip.text.y = element_text(size = 16), legend.title=element_text(size=18,face="bold"), 
        legend.text=element_text(size=18))+
#  xlab("Architecture") + 
  scale_y_continuous(labels = scales::percent)+
  # ylab("Change (1-score/Pmean)")
  ylab("Cheaper Cost")+
  labs(fill = "Cost\nImprovement")
Figure_Impact_Budget
ggsave(Figure_Impact_Budget, filename = file.path('Figures', 'Impact_Budget.png'),width = 6,height = 5,dpi = 1200)

## Bar Plot Impact on Expert Reliance
sumBar$ReduceExpert <- factor(sumBar$ReduceExpert, level = c("Yes","Minor","No"))

Figure_Impact_ReduceExpert <- ggplot(sumBar, aes(x=Architecture, y=Counter, fill=ReduceExpert))+
  theme_bw()+
  geom_bar(stat = "identity",position = "fill")+
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=16),
        axis.title.x = element_text(size=16,face="bold"),axis.title.y = element_text(size=16,face="bold"),
        strip.text.y = element_text(size = 16), legend.title=element_text(size=18,face="bold"), 
        legend.text=element_text(size=18))+
  xlab("Architecture") + 
  scale_y_continuous(labels = scales::percent)+
  labs(fill = "Meaningful\nReduction\nof Expert\nReliance")+
  # ylab("Change (1-score/Pmean)")
  ylab("Reduced Expert Effort")
Figure_Impact_ReduceExpert
ggsave(Figure_Impact_ReduceExpert, filename = file.path('Figures', 'Impact_Expert.png'),width = 6,height = 5,dpi = 1200)

## Bar Plot on Dominance
sumBar$Dominant <- factor(sumBar$Dominant, level = c("Yes","Fuzzy","No"))

Figure_Impact_Dominant <- ggplot(sumBar, aes(x=Architecture, y=Counter, fill=Dominant))+
  theme_bw()+
  geom_bar(stat = "identity",position = "fill")+
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=16),
        axis.title.x = element_text(size=16,face="bold"),axis.title.y = element_text(size=16,face="bold"),
        strip.text.y = element_text(size = 16), legend.title=element_text(size=18,face="bold"), 
        legend.text=element_text(size=18))+
  xlab("Architecture") + 
  scale_y_continuous(labels = scales::percent)+
  # ylab("Change (1-score/Pmean)")
  ylab("Dominant Solution")+
  labs(fill = "Dominant\nSolutions")
Figure_Impact_Dominant
ggsave(Figure_Impact_Dominant, filename = file.path('Figures', 'Impact_Dominant.png'),width = 6,height =5,dpi = 1200)

# This is PNAS Plot 6b 
Zoe_Plot <- plot_grid(Figure_Impact_Dominant,Figure_Impact_Performance,Figure_Impact_Budget,Figure_Impact_ReduceExpert,ncol = 1,nrow = 4,hjust = -0.5)
ggsave(Zoe_Plot, filename = file.path('Figures', 'Zoe_Plot.png'),width = 9,height = 10,dpi = 1200)


#Sensitivity Plot for the best quadrant
sumstatsDecomp["Match"]<-0 # following lines of code mark the architecture-contract pairs with the same notation in the previous plot.
sumstatsDecomp <-  sumstatsDecomp %>%
  mutate(Match = case_when((Architecture == "LP" & (Assignment == "PA"| Assignment == "SA"))|(Architecture == "DS" & Assignment == "PA")|
                             (Architecture == "DAP" & (Assignment == "SSA"|Assignment == "PSA"|Assignment == "PPA"))~"Ama",
                           ((Architecture == "DAP" & (Assignment == "SAA"|Assignment == "SAS"|Assignment == "SPP"|Assignment == "SPS"|
                                                        Assignment == "SSP"|Assignment == "SSS"))|(Architecture == "DS" & (Assignment == "SP"|Assignment == "SS")))~"Sp",
                           ((Architecture=="DAP" & (Assignment == "SAP"|Assignment == "SPA"))|(Architecture == "DS" & Assignment == "SA"))~"Ideal"))


sumstatsDecomp[is.na(sumstatsDecomp)] = 0 # reset the NAs to zero for plotting later


Figure2f <- ggplot(filter(sumstatsDecomp, Architecture != "H"))+
  geom_point(aes(x = Score, y = cost, color = Match, size = Fraction))+
  #  geom_errorbarh(aes(xmin=Score-sd, xmax=Score+sd,y = cost),height=1)+
  #  scale_size_continuous(range = c(4, 8))+
  geom_text(aes(x = Score, y = cost,label=Assignment),nudge_x = 0.25, nudge_y =-1.5, angle=45)+
  labs(color = "Match",size= "Fraction of Expert Usage")+
  scale_color_manual(values = c("#AAAAAA","#D30000", "#E69F00", "#00CED1"), labels=c("Baseline","Proper Use of Amateurs","Ideal Use of all Solver Types","Speacialists Well-Matched"))+
  geom_hline(yintercept = sumstatsDecomp$cost[4])+
  geom_vline(xintercept = mean)+
  ggtitle("Sensitivity - 550YD Hole") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  guides(fill=guide_legend(nrow=3,byrow=TRUE))+
  xlab("Score of the Innovation Strategy") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Cost of the Innovation Strategy")
#  xlim(NA,mean)+ # set X limit
#  ylim(NA,sumstatsDecomp$cost[4]) # set y limit
Figure2f
ggsave(Figure2f, filename = file.path('Figures', 'Sensitivity.png'),width = 8,height = 8,dpi = 1200)


Figure2k <- ggplot(filter(sumstatsDecomp, Architecture != "H"))+
  geom_point(aes(x=Fraction, y=cost, size = mean - Score, color = Match))+
  labs(size =  "Goodness of  \nPerformance  \nCompared to Pro", color = "Contract Organization")+
  scale_color_manual(values = c("#AAAAAA","#D30000", "#E69F00", "#00CED1"), labels=c("Baseline","Proper Use of Amateurs","Ideal Use of all Solver Types","Speacialists Well-Matched"))+
  ggtitle("Cost vs. Fraction of Professional Effort") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14))+
  xlab("Fraction of Professional Effort") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Cost")
#  ylim(0,0.8)
#geom_hline(yintercept = mean)
Figure2k
ggsave(Figure2k, filename = file.path('Figures', 'Cost vs. Fraction of Pro_color.png'),width = 6,height = 6,dpi = 1200)




Figure2i <- ggplot(filter(sumstatsDecomp, Architecture != "H"))+
  theme_bw()+
  geom_point(aes(x=Fraction, y=Score, size = cost, color = Match))+
  labs(size =  "Cost", color = "Contract Organization")+
  scale_color_manual(values = c("#AAAAAA","#D30000", "#E69F00", "#00CED1"), labels=c("Baseline","Proper Use of Amateurs","Ideal Use of all Solver Types","Speacialists Well-Matched"))+
  ggtitle("Performance vs. Fraction of Professional Effort") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14))+
  xlab("Fraction of Professional Effort") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Performance")
#  ylim(0,0.8)
#geom_hline(yintercept = mean)
Figure2i
ggsave(Figure2i, filename = file.path('Figures', 'Performance vs. Fraction of Pro_color.png'),width = 6,height = 6,dpi = 1200)


Figure2j <- ggplot(filter(sumstatsDecomp, Architecture != "H"))+
  geom_point(aes(x=Fraction, y=Score, shape = Architecture, color = Match))+
  labs(shape =  "Architecture", color = "Contract Organization")+
  scale_color_manual(values = c("#AAAAAA","#D30000", "#E69F00", "#00CED1"), labels=c("Baseline","Proper Use of Amateurs","Ideal Use of all Solver Types","Speacialists Well-Matched"))+
  ggtitle("Performance vs. Fraction of Professional Effort") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14))+
  xlab("Fraction of Professional Effort") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Performance")+
  theme_bw()
#  ylim(0,0.8)
#geom_hline(yintercept = mean)
Figure2j
ggsave(Figure2j, filename = file.path('Figures', 'Performance vs. Fraction of Pro_color2.png'),width = 6,height = 6,dpi = 1200)


Figure2k <- ggplot(filter(sumstatsDecomp, Architecture != "H"))+
  geom_point(aes(x=Fraction, y=Score, shape = Architecture, size=cost, color = Match))+
  labs(shape =  "Architecture", size="Cost", color = "Contract Organization")+
  scale_color_manual(values = c("#AAAAAA","#D30000", "#E69F00", "#00CED1"), labels=c("Baseline","Proper Use of Amateurs","Ideal Use of all Solver Types","Speacialists Well-Matched"))+
  scale_size_continuous(breaks = c(30,50,70,80,90), range = c(0.5, 5))+
  geom_hline(yintercept = mean)+
  ggtitle("Performance vs. Fraction of Professional Effort") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14))+
  xlab("Fraction of Professional Effort") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Performance")+
  theme_bw()
#  ylim(0,0.8)
#geom_hline(yintercept = mean)
Figure2k

Figure2l <- ggplot(filter(sumstatsDecomp, Architecture != "H"))+
  geom_point(aes(x=Fraction, y=Score, shape = Architecture, size=cost, color = Match))+
  labs(shape =  "Architecture", size="Cost", color = "Contract Organization")+
  scale_color_manual(values = c("#AAAAAA","#D30000", "#E69F00", "#00CED1"), labels=c("Baseline","Proper Use of Amateurs","Ideal Use of all Solver Types","Speacialists Well-Matched"))+
  scale_size_continuous(breaks = c(30,50,70,80,90), range = c(0.5, 5))+
  geom_hline(yintercept = mean)+
  ggtitle("Performance vs. Fraction of Professional Effort") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14))+
  xlab("Fraction of Professional Effort") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Performance")+
  theme_bw()
#  ylim(0,0.8)
#geom_hline(yintercept = mean)
Figure2l

ggsave(Figure2k, filename = file.path('Figures', 'Performance vs. Fraction of Pro_color3.png'),width = 6,height = 6,dpi = 1200)
## Figure 3 - Perforance vs. fraction of pro effort for the good ones.

# Strokes<-  Strokes %>%
#   mutate(Drive_Assignment = ifelse(((Architecture=="DAP"|Architecture=="DS")&(substring(Strokes$Assignment,1,1)=="S")),"Specialist",ifelse(((Architecture=="DAP"|Architecture=="DS")& substring(Strokes$Assignment,1,1)=="A"),"Amateur",
#                                                                                                                                            ifelse(((Architecture=="DAP"|Architecture=="DS")& (substring(Strokes$Assignment,1,1)=="P")),"Pro","NA"))))%>%
#   mutate(Putt_Assignment = ifelse(((Architecture=="DAP" &(substring(Strokes$Assignment,3,3)=="S"))|(Architecture=="LP" &(substring(Strokes$Assignment,2,2)=="S"))),"Specialist",
#                                   ifelse(((Architecture=="DAP" &(substring(Strokes$Assignment,3,3)=="A"))|(Architecture=="LP" &(substring(Strokes$Assignment,2,2)=="A"))),"Amateur",
#                                          ifelse(((Architecture=="DAP" &(substring(Strokes$Assignment,3,3)=="P"))|(Architecture=="LP" &(substring(Strokes$Assignment,2,2)=="P"))),"Pro","NA"))))%>%
#   mutate(CompScore = 1-Strokes$Score/mean)%>%
#   mutate(CompCost = 1-Strokes$cost/mean_cost)

## Thus us where we mark the module assignments
Strokes<-  Strokes %>%
          mutate(Drive_Assignment = ifelse(((Architecture=="DAP"|Architecture=="DS")&(substring(Strokes$Assignment,1,1)=="S")),"Specialist",ifelse(((Architecture=="DAP"|Architecture=="DS")& substring(Strokes$Assignment,1,1)=="A"),"Amateur",
                 ifelse(((Architecture=="DAP"|Architecture=="DS")& (substring(Strokes$Assignment,1,1)=="P")),"Pro","NA"))))%>%
          mutate(Putt_Assignment = ifelse(((Architecture=="DAP" &(substring(Strokes$Assignment,3,3)=="S"))|(Architecture=="LP" &(substring(Strokes$Assignment,2,2)=="S"))),"Specialist",
                                          ifelse(((Architecture=="DAP" &(substring(Strokes$Assignment,3,3)=="A"))|(Architecture=="LP" &(substring(Strokes$Assignment,2,2)=="A"))),"Amateur",
                                          ifelse(((Architecture=="DAP" &(substring(Strokes$Assignment,3,3)=="P"))|(Architecture=="LP" &(substring(Strokes$Assignment,2,2)=="P"))),"Pro","NA"))))%>%
          mutate(Long_Assignment = ifelse(((Architecture=="LP")&(substring(Strokes$Assignment,1,1)=="S")),"Specialist",ifelse(((Architecture=="LP")&substring(Strokes$Assignment,1,1)=="A"),"Amateur",
                                          ifelse(((Architecture=="LP")& (substring(Strokes$Assignment,1,1)=="P")),"Pro","NA"))))%>%
          mutate(Short_Assignment = ifelse(((Architecture=="DS")&(substring(Strokes$Assignment,2,2)=="S")),"Specialist",ifelse(((Architecture=="DS")&substring(Strokes$Assignment,2,2)=="A"),"Amateur",
                                                                                                                      ifelse(((Architecture=="DS")& (substring(Strokes$Assignment,2,2)=="P")),"Pro","NA"))))%>%
          mutate(CompScore = 1-Strokes$Score/mean)%>%
          mutate(CompCost = 1-Strokes$cost/mean_cost)
        
#ifelse((Architecture=="DAP"|Architecture=="DS"),substring(Strokes$Assignment,1,1),ifelse((Architecture=="H"&Assignment == "P"),"Benchmark","NA")))%>%
Strokes$Drive_Assignment = factor(Strokes$Drive_Assignment, levels = c("Pro","Amateur","Specialist","NA"))
Strokes$Putt_Assignment = factor(Strokes$Putt_Assignment, levels = c("Pro","Amateur","Specialist","NA"))
Strokes$Long_Assignment = factor(Strokes$Long_Assignment, levels = c("Pro","Amateur","Specialist","NA"))
Strokes$Short_Assignment = factor(Strokes$Short_Assignment, levels = c("Pro","Amateur","Specialist","NA"))



sumstats_TT <- summarySE(Strokes, measurevar="Score", groupvars=c("Architecture", "Assignment","Tournament_type","Drive_Assignment","Putt_Assignment","Long_Assignment","Short_Assignment"))
sumcost_TT <- summarySE(Strokes,measurevar = "cost",groupvars=c("Architecture", "Assignment","Tournament_type","Drive_Assignment","Putt_Assignment","Long_Assignment","Short_Assignment"))
sumstats_TT$cost <- sumcost_TT$cost
sumstats_TT <- sumstats_TT %>%
mutate(CompScore = 1-sumstats_TT$Score/mean)%>%
  mutate(CompCost = 1-sumstats_TT$cost/mean_cost)


Figure2_Comp_Drive <- ggplot(filter(Strokes,Drive_Assignment != "NA"))+
  theme_bw()+  
  #  geom_hline(yintercept = 0)+
  #  geom_text(aes(x = 0, y = 0, label = "AAPL")) + 
  #  annotate("text", label = "Pro Benchmark", x = 1, y = 2) +
  #  annotate(geom = "text", x = 4.1, y = 0, label = "Pro Benchmark", hjust = "left")+
  #  geom_text(aes(x=0, y=0, label="Pro Benchmark"), color="orange",size=7 , angle=45, fontface="bold" )+
  #  geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Drive_Assignment, y = CompScore))+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Performance Impact of Drive Assignment") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Normalized Performance")+
  xlab("Drive Assignment") 
Figure2_Comp_Drive
ggsave(Figure2_Comp_Drive, filename = file.path('Figures', 'Specialist Drive.png'),width = 6,height = 6,dpi = 1200)

Figure2_Comp_Drive_cost <- ggplot(filter(Strokes,Drive_Assignment != "NA"))+
  theme_bw()+  
  #geom_hline(yintercept = 0)+
  #  geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Drive_Assignment, y = CompCost))+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Cost Impact of Drive Assignment") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Normalized Cost")  +
  xlab("Drive Assignment") 
Figure2_Comp_Drive_cost
ggsave(Figure2_Comp_Drive_cost, filename = file.path('Figures', 'Specialist Drive_cost.png'),width = 6,height = 6,dpi = 1200)  

Figure2_Comp_Putt <- ggplot(filter(Strokes,Putt_Assignment != "NA"))+
  theme_bw()+  
  #  geom_hline(yintercept = 0)+
  #  geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Putt_Assignment, y = CompScore))+
  #  geom_boxplot(aes(x = Putt_Assignment,y = CompCost),position_dodge(width = 0.9))+
  #  facet_grid(CompScore~CompCost)+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Performance Impact of Putt Assignment") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Normalized Performance")  +
  xlab("Putt Assignment") 
Figure2_Comp_Putt
ggsave(Figure2_Comp_Putt, filename = file.path('Figures', 'Amateur Putt.png'),width = 6,height = 6,dpi = 1200)

Figure2_Comp_Putt_cost <- ggplot(filter(Strokes,Putt_Assignment != "NA"))+
  theme_bw()+  
  #geom_hline(yintercept = 0)+
  #  geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Putt_Assignment, y = CompCost))+
  #  geom_boxplot(aes(x = Putt_Assignment,y = CompCost),position_dodge(width = 0.9))+
  #  facet_grid(CompScore~CompCost)+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Cost Impact of Putt Assignment") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Normalized Cost")  +
  xlab("Putt Assignment") 
Figure2_Comp_Putt_cost
ggsave(Figure2_Comp_Putt_cost, filename = file.path('Figures', 'Amateur Putt_Cost.png'),width = 6,height = 6,dpi = 1200)

Strat_Plot_normalized <- plot_grid(Figure2_Comp_Drive,Figure2_Comp_Drive_cost,Figure2_Comp_Putt,Figure2_Comp_Putt_cost,ncol = 2,nrow = 2,hjust = -0.5)
ggsave(Strat_Plot_normalized, filename = file.path('Figures', 'Start_Plot.png'),width = 12,height = 8,dpi = 1200)

## I think this plot looks better without normalization

Figure2_Comp_Drive_reg <- ggplot(filter(Strokes,Drive_Assignment != "NA"))+
  theme_bw()+  
#  geom_hline(yintercept = mean,linetype="dashed",color="red")+
  geom_boxplot(aes(x = Drive_Assignment, y = CompScore))+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Drive") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Performance") +
  xlab("Drive Assignment") 
Figure2_Comp_Drive_reg
ggsave(Figure2_Comp_Drive_reg, filename = file.path('Figures', 'Specialist Drive.png'),width = 6,height = 6,dpi = 1200)

Figure2_Comp_Drive_cost_reg <- ggplot(filter(Strokes,Drive_Assignment != "NA"))+
  theme_bw()+  
#  geom_hline(yintercept = mean_cost,linetype="dashed",color="red")+
  #  geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Drive_Assignment, y = CompCost))+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Drive") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.text = element_text(size=12),legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Cost")+
  xlab("Drive Assignment") 
Figure2_Comp_Drive_cost_reg
ggsave(Figure2_Comp_Drive_cost_reg, filename = file.path('Figures', 'Specialist Drive_cost.png'),width = 6,height = 6,dpi = 1200)  

Figure2_Comp_Putt_reg <- ggplot(filter(Strokes,Putt_Assignment != "NA"))+
  theme_bw()+  
#  geom_hline(yintercept = mean,linetype="dashed",color="red")+
  #  geom_hline(yintercept = 0)+
  #  geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Putt_Assignment, y = CompScore))+
  #  geom_boxplot(aes(x = Putt_Assignment,y = CompCost),position_dodge(width = 0.9))+
  #  facet_grid(CompScore~CompCost)+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Putt") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Performance")  +
  xlab("Putt Assignment") 
Figure2_Comp_Putt_reg
ggsave(Figure2_Comp_Putt_reg, filename = file.path('Figures', 'Amateur Putt.png'),width = 6,height = 6,dpi = 1200)

Figure2_Comp_Putt_cost_reg <- ggplot(filter(Strokes,Putt_Assignment != "NA"))+
  theme_bw()+  
#  geom_hline(yintercept = mean_cost,linetype="dashed",color="red")+
  #geom_hline(yintercept = 0)+
  #  geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Putt_Assignment, y = CompCost))+
  #  geom_boxplot(aes(x = Putt_Assignment,y = CompCost),position_dodge(width = 0.9))+
  #  facet_grid(CompScore~CompCost)+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Putt") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Cost")+
  xlab("Putt Assignment") 
Figure2_Comp_Putt_cost_reg
ggsave(Figure2_Comp_Putt_cost_reg, filename = file.path('Figures', 'Amateur Putt_Cost.png'),width = 6,height = 6,dpi = 1200)

Figure2_Comp_Long_reg <- ggplot(filter(Strokes,Long_Assignment != "NA"))+
  theme_bw()+  
#  geom_hline(yintercept = mean,linetype="dashed",color="red")+
  geom_boxplot(aes(x = Long_Assignment, y = CompScore))+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Long") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Performance") +
  xlab("Long Assignment") 
Figure2_Comp_Long_reg
ggsave(Figure2_Comp_Long_reg, filename = file.path('Figures', 'Specialist Drive.png'),width = 6,height = 6,dpi = 1200)

Figure2_Comp_Long_cost_reg <- ggplot(filter(Strokes,Long_Assignment != "NA"))+
  theme_bw()+  
#  geom_hline(yintercept = mean_cost,linetype="dashed",color="red")+
  #  geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Long_Assignment, y = CompCost))+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Long") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Cost")+
  xlab("Long Assignment") 
Figure2_Comp_Long_cost_reg
ggsave(Figure2_Comp_Long_cost_reg, filename = file.path('Figures', 'Specialist Drive_cost.png'),width = 6,height = 6,dpi = 1200)  

Figure2_Comp_Short_reg <- ggplot(filter(Strokes,Short_Assignment != "NA"))+
  theme_bw()+  
#  geom_hline(yintercept = mean,linetype="dashed",color="red")+
  geom_boxplot(aes(x = Short_Assignment, y = CompScore))+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Short") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Performance") +
  xlab("Short Assignment") 
Figure2_Comp_Short_reg
ggsave(Figure2_Comp_Short_reg, filename = file.path('Figures', 'Specialist Drive.png'),width = 6,height = 6,dpi = 1200)

Figure2_Comp_Short_cost_reg <- ggplot(filter(Strokes,Short_Assignment != "NA"))+
  theme_bw()+  
#  geom_hline(yintercept = mean_cost,linetype="dashed",color="red")+
  #  geom_hline(yintercept = meanP100)+
  geom_boxplot(aes(x = Short_Assignment, y = CompCost))+
  #  facet_grid(cols = vars(Architecture),scales = "free")+
  ggtitle("Short") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14),legend.position = "bottom",legend.box="vertical",legend.margin=margin())+
  # ylab("Change (1-score/Pmean)")
  ylab("Cost")+
  xlab("Short Assignment") 
Figure2_Comp_Short_cost_reg
ggsave(Figure2_Comp_Short_cost_reg, filename = file.path('Figures', 'Specialist Drive_cost.png'),width = 6,height = 6,dpi = 1200)  



Strat_Plot_reg <- plot_grid(Figure2_Comp_Drive_reg,Figure2_Comp_Drive_cost_reg,Figure2_Comp_Putt_reg,Figure2_Comp_Putt_cost_reg,ncol = 2,nrow = 2,hjust = -0.5)
ggsave(Strat_Plot_reg, filename = file.path('Figures', 'Start_Plot_reg.png'),width = 12,height = 8,dpi = 1200)

Plot_ModuleSolver_Perf <- plot_grid(Figure2_Comp_Drive_reg,Figure2_Comp_Putt_reg,Figure2_Comp_Long_reg,Figure2_Comp_Short_reg,ncol = 4,nrow = 1,hjust = -0.5)
ggsave(Plot_ModuleSolver_Perf, filename = file.path('Figures', 'AllModules_reg.png'),width = 10,height = 5,dpi = 1200)

Plot_ModuleSolver_Cost <- plot_grid(Figure2_Comp_Drive_cost_reg,Figure2_Comp_Putt_cost_reg,Figure2_Comp_Long_cost_reg,Figure2_Comp_Short_cost_reg,ncol = 4,nrow = 1,hjust = -0.5)
ggsave(Plot_ModuleSolver_Cost, filename = file.path('Figures', 'AllModules_reg_cost.png'),width = 10,height = 5,dpi = 1200)

Plot_ModuleSolver_Aggregate <- plot_grid(Plot_ModuleSolver_Perf,Plot_ModuleSolver_Cost,ncol = 1,nrow = 2,hjust = -0.5)
ggsave(Plot_ModuleSolver_Aggregate, filename = file.path('Figures', 'AllModules_Joint.png'),width = 10,height = 5,dpi = 1200)



  Good <- filter(sumstatsDecomp,
                 (Assignment == "P"&Tournament_type=="1")|
                 (Assignment == "PA"& Architecture =="LP")|
                 (Assignment == "SA"& Architecture =="LP")|
                 (Assignment == "SP"& Architecture =="LP")|
                 (Assignment == "SA"& Architecture =="DS")|
                 (Assignment == "SP"& Architecture =="DS")|
                 (Assignment == "PPA")|
                 (Assignment == "SAP")|
                 (Assignment == "SPA")|
                 (Assignment == "SPP")|
                 (Assignment == "SPS")|
                 (Assignment == "SSA")|
                 (Assignment == "SSP"))


Good$FractionPro <- c(Good$Sub1[1]/Good$Score[1],
                      Good$Sub1[2]/Good$Score[2],
                      0,
                      Good$Sub2[4]/Good$Score[4],
                      (Good$Sub1[5]+Good$Sub2[5])/Good$Score[5],
                      Good$Sub3[6]/Good$Score[6],
                      Good$Sub2[7]/Good$Score[7],
                      (Good$Sub2[8]+Good$Sub3[8])/Good$Score[8],
                      Good$Sub2[9]/Good$Score[9],
                      0,
                      Good$Sub3[11]/Good$Score[11],
                      0,
                      Good$Sub2[13]/Good$Score[13])

Good$FractionAm <- c(0,
                      Good$Sub2[2]/Good$Score[2],
                      Good$Sub2[3]/Good$Score[3],
                      0,
                      Good$Sub3[5]/Good$Score[5],
                      Good$Sub2[6]/Good$Score[6],
                      Good$Sub3[7]/Good$Score[7],
                      0,
                      0,
                      Good$Sub3[10]/Good$Score[10],
                      0,
                      Good$Sub2[12]/Good$Score[12],
                      0)

# I'm plotting fraction of strokes taken by an amateur on the y-axis and fraction
# strokes taken by a pro on the x axis (the remainder is specialist). The size of
# the point is the score (bigger is better here)
Figure3 <- ggplot(Good)+
  geom_point(aes(x=FractionPro, y=FractionAm, size = mean - Score, color = Architecture))+
  labs(size =  "Goodness of  \nPerformance  \nCompared to Pro", color = "Architecture")+
  ggtitle("Fraction of Efforts") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14))+
  xlab("Fraction of Professional Effort") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Fraction of Amateur Effort")+
  ylim(0,0.8)
  #geom_hline(yintercept = mean)
Figure3
ggsave(Figure3, filename = file.path('Figures', 'Fraction of Efforts.png'),width = 6,height = 6,dpi = 1200)



## alternative Score-Performance with fraction

Figure2g <- ggplot(Good)+
  geom_point(aes(x=FractionPro, y=cost, size = mean - Score, color = Architecture))+
  labs(size =  "Goodness of  \nPerformance  \nCompared to Pro", color = "Architecture")+
  ggtitle("Cost vs. Fraction of Professional Effort") +
  theme(plot.title = element_text(size=16,face="bold", hjust = 0.5),axis.text=element_text(size=14),
        axis.title.x = element_text(size=14,face="bold"),axis.title.y = element_text(size=14,face="bold"),
        strip.text.y = element_text(size = 14))+
  xlab("Fraction of Professional Effort") + 
  # ylab("Change (1-score/Pmean)")
  ylab("Cost")
#  ylim(0,0.8)
#geom_hline(yintercept = mean)
Figure2g
ggsave(Figure2g, filename = file.path('Figures', 'Cost vs. Fraction of Pro Efforts.png'),width = 6,height = 6,dpi = 1200)


# 
#Subproblems <- filter(Subproblems,distance == "200"|distance == "650"|distance == "20")

Figure4a <- ggplot(filter(Subproblems, Subproblem_type != "Drive"))+
 geom_density(aes(x = Result))+
 facet_grid(rows = vars(Solver_type),cols = vars(Subproblem_type),scales = "free")+
 xlab("Number of strokes to complete subproblem") +
 ylab("Probability density")
Figure4a
ggsave(Figure4a, filename = file.path('Figures', 'Density of Solver Performance.png'),width = 6,height = 6,dpi = 1200)

Figure4 <- ggplot(filter(Subproblems, Subproblem_type != "Drive"))+
  theme_bw()+
  geom_boxplot(aes(x = distance, y = Result))+
  facet_grid(cols = vars(Solver_type),rows = vars(Subproblem_type),scales = "free")+
  ggtitle("Number of Strokes Based on Distance") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14))+
  ylab("Number of Strokes to Complete Module") +
  xlab("Distance")#+
  #xlim(0,8)

Figure4
ggsave(Figure4, filename = file.path('Figures', 'Strokes w.r.t Solvers.png'),width = 12,height = 8,dpi = 1200)

# 
Figure5 <- ggplot(Shots)+
  theme_bw()+
  geom_density(aes(x = Result))+
  facet_grid(rows = vars(Solver_type),cols = vars(Shot_type),scales = "free")+
  ggtitle("Solver Probability Densities Based on Distance") +
  theme(plot.title = element_text(size=16, hjust = 0.5),axis.text=element_text(size=10),
        axis.title.x = element_text(size=14),axis.title.y = element_text(size=14),
        strip.text.y = element_text(size = 14))+
  ylab("Probability density") +
  xlab("distance")+
  ylim(0,0.1)
#xlim(0,8)

Figure5
ggsave(Figure5, filename = file.path('Figures', 'Solver Probability Densities.png'),width = 12,height = 8,dpi = 1200)

# 
## Test Plots

# # 1. Compare H to DS for single pros to show impact of removing X2.
# # The boxplot version
# DecompStrokesP1R2 <- filter(DecompStrokes,(Architecture == "DS"&Rule == "Optimal")|Architecture =="H")
# DecompStrokesP1R2 <- filter(DecompStrokesP1R2,Tournament_type =="One"|Tournament_type =="Ten")
# DecompStrokesP1R2 <- filter(DecompStrokesP1R2,Assignment_type == "Pro")
# #DecompStrokesA <- filter(DecompStrokes,Assignment_type == "Amateur")
# 
# Test1a <- ggplot(DecompStrokesP1R2)+
#   geom_boxplot(aes(x=Architecture,y=Score))+#, color = Rule))+
#   facet_grid(cols = vars(Tournament_type), rows = vars(Assignment_type), scales = "free")
# 
# Test1a
# 
# #the point plot version
# Test1 <- filter(sumstatsDecomp, (Architecture == "DS"&Rule == "Optimal")|Architecture =="H")
# Test1 <- filter(Test1,Tournament_type =="One"|Tournament_type =="Ten")
# Test1 <- filter(Test1,Assignment == "P"|Assignment == "PP")
# Test1$Score <- Test1$Score-sumstatsDecomp$Score[4]
# 
# Test1plot <- ggplot(Test1)+
#   geom_hline(aes(yintercept = 0))+
#   geom_errorbar(aes(x = Architecture, y = Score, ymin=Score-ci, ymax=Score+ci),
#                 width=.2,                    # Width of the error bars
#                 position=position_dodge(.9))+
#   geom_point(aes(x=Architecture, y=Score,
#                  size=2 ))+#position=position_dodge(), stat="identity") +
#   facet_grid(cols = vars(Tournament_type),scales = "free")+
#   theme(legend.position = "none") #removes legend
# Test1plot
# 
# # 2. Compare H to LP, for three rules of Ten Ams,
# DecompStrokesA10 <- filter(DecompStrokes,Assignment_type == "Amateur"&Tournament_type =="Ten")
# 
# Test2a <- ggplot(DecompStrokesA10)+
#   geom_boxplot(aes(x=Rule,y=Score))+#,color = Architecture))
#   facet_grid(cols = vars(Architecture),scales = "free",space = "free")
# Test2a
# 
# Test2A <- filter(sumstatsDecomp, (Assignment == "A"|Assignment == "AA")&Tournament_type =="Ten")
# Test2A <- filter(Test2A, Architecture != "R")
# 
# Test2A$Score <- Test2A$Score - sumstatsDecomp$Score[8]
# Test2plotA <- ggplot(Test2A)+
#   geom_hline(aes(yintercept = 0))+
#   geom_errorbar(aes(x=Rule,y=Score, ymin=Score-ci, ymax=Score+ci),
#         width=.2,                    # Width of the error bars
#         position=position_dodge(.9))+
#   geom_point(aes(x = Rule, y=Score,size = cost))+
#   facet_grid(cols = vars(Architecture), scales = "free",space="free")#+
#   #theme(legend.position = "none")
# Test2plotA
# 
# Test2P <- filter(sumstatsDecomp, (Assignment == "P"|Assignment == "PP")&Tournament_type =="Ten")
# Test2P <- filter(Test2P, Architecture != "R")
# 
# Test2P$Score <- Test2P$Score - sumstatsDecomp$Score[11]
# Test2plotP <- ggplot(Test2P)+
#   geom_hline(aes(yintercept = 0))+
#   geom_errorbar(aes(x=Rule,y=Score, ymin=Score-ci, ymax=Score+ci),
#                 width=.2,                    # Width of the error bars
#                 position=position_dodge(.9))+
#   geom_point(aes(x = Rule, y=Score,size = cost))+
#   facet_grid(cols = vars(Architecture), scales = "free",space="free")+
#   theme(legend.position = "none")
# Test2plotP
# 
# DecompTestX3 <- filter(DecompStrokes,Assignment_type =="Amateur"&Tournament_type =="Ten")
# TestX3 <- ggplot(DecompTestX3)+
#   geom_boxplot(aes(x=Rule,y=Score))+#, color = Rule))+
#   #geom_point(aes(x=Rule,y=cost))+
#   facet_grid(cols = vars(Architecture), scales = "free",space = "free")
# 
# TestX3
# 
# TestX3b <- ggplot(DecompStrokes)+
#   geom_point(aes(y=Score,x=cost, color = Rule,))+
#   facet_grid(cols = vars(Architecture), rows = vars(Tournament_type),scales = "free",space = "free")
# 
# TestX3b
# 
# ############################
# # 3. Costs of decomposing
# Test3 <- ggplot(sumstatsDecomp,aes(y = cost, x=Architecture,fill = Rule))+
#   geom_bar(stat = "identity",position=position_dodge())+
#   facet_grid(cols = vars(Tournament_type),rows = vars(Assignment_type), scales = "free")
# Test3
# 
# ############################
# # 4. Benefits due to variance reduction.
# Test4 <- filter(sumstatsDecomp, Assignment_type != "Hybrid")
# 
# Test4plot <- ggplot(Test4)+
#   geom_errorbar(aes(x = Tournament_type, y = Score, ymin = Score - ci, ymax = Score + ci),
#                 width = .1)+
#   geom_point(aes(x = Tournament_type, y = Score,
#                  color = Rule))+
#   facet_grid(cols = vars(Architecture),rows = vars(Assignment_type), scales = "free")
# Test4plot
# 
# #####################
# # 5. Schedule improvements
# Test5 <- filter(sumstatsDecomp,Tournament_type=="One"&Assignment_type != "Hybrid")
# 
# Test5plot <- ggplot(Test5)+
#   geom_errorbar(aes(x = Rule, y = sched_steady, ymin = sched_steady - ci_ss, ymax = sched_steady + ci_ss),
#                 width = .1)+
#   geom_point(aes(x = Rule, y = sched_steady,
#                  size = 1))+
#   scale_y_continuous(trans='log10')+
#   geom_errorbar(aes(x = Rule, y = sched_part, ymin = sched_part - ci_ss, ymax = sched_part + ci_ss),
#                 width = .01,
#                 position = position_dodge(1), color = "red")+
#   geom_point(aes(x = Rule, y = sched_part,
#                  size = 1, color = "red"))+
#   facet_grid(cols = vars(Architecture),rows = vars(Assignment_type), scales = "free",space = "free")+
#   theme(legend.position = "none")
# Test5plot
# 
# 
# 
# #####################################
# # What about when you only use Amateurs sometimes...
# 
# Test7 <- filter(sumstatsDecomp,!(Assignment == "P" & Tournament_type != "1")&!(Assignment == "PP" & Tournament_type != "1"))
# Test7part <- filter(Test7,(Tournament_type == "10"&Assignment_type =="Hybrid")|(Assignment_type =="Pro")|(Assignment_type == "Amateur"&Tournament_type == "10"))
# Test7ass <- filter(Test7part,Architecture != "R")#&Architecture!="H")
# 
# Test7Plot <- ggplot(Test7ass) +
#   geom_errorbar(aes(x = Assignment, y = Score, ymin = Score - ci, ymax = Score + ci),
#                 width = .1,
#                 position = position_dodge(1))+
#   geom_point(aes(x = Assignment, y = Score,
#                  color = Rule, size = cost))+
#   geom_hline(aes(yintercept = Test7$Score[6]))+
#   geom_hline(aes(yintercept = Test7$Score[8]))+
#   facet_grid(cols = vars(Architecture),scales = "free",space = "free")#+
# #theme(legend.position = "none")
# Test7Plot
# 
# # Is it worth the cost?
# 
# Test7cost <- ggplot(Test7) +
#   geom_errorbar(aes(x = cost, y = Score, ymin=Score-ci, ymax=Score+ci),
#                 width=.2#,                    # Width of the error bars
#                 #position=position_dodge(.9)
#                 )+
#   geom_point(aes(x=cost, y=Score, 
#                  shape=Architecture, 
#                  color = Assignment,
#                  size = Tournament_type))#+#+position=position_dodge(), stat="identity") 
#   #facet_grid(cols = vars(Architecture),scales = "free",space = "free")
#   #xlim(0,200)
# 
# Test7cost
# 
# Test7sched <- ggplot(Test7) +
#   geom_errorbar(aes(x = cost, y = sched_steady, ymin=sched_steady-ci_ss, ymax=sched_steady+ci_ss),
#                 width=.2#,                    # Width of the error bars
#                 #position=position_dodge(.9)
#   )+
#   geom_point(aes(x=cost, y=sched_steady, 
#                  shape=Architecture, 
#                  color = Assignment,
#                  size=Tournament_type ))+#+#+position=position_dodge(), stat="identity") 
# #facet_grid(cols = vars(Architecture),scales = "free",space = "free")
# #ylim(3.5,11)
#   scale_y_continuous(trans='log10')
# 
# Test7sched
# 
# Test7schedcost <- ggplot(Test7) +
#   geom_point(aes(x=cost, y=Score, 
#                  shape=Architecture, 
#                  color = Assignment_type,
#                  size=sched_steady ))+ #+#+position=position_dodge(), stat="identity") 
#   geom_errorbar(aes(x = cost, y = Score, ymin=Score-ci, ymax=Score+ci, color = Assignment_type),
#                 width=2 #,                    # Width of the error bars
#                 #position=position_dodge(.9)
#   )
#   
# #facet_grid(cols = vars(Architecture),scales = "free",space = "free")
# #xlim(0,200)
# 
# Test7schedcost
# 
# ###############################################
# # 8. Solving path
# RPath <- filter(DecompPath, Architecture == "R")
# HPath <- filter(DecompPath, Architecture == "H")
# LPPath <- filter(DecompPath, Architecture == "LP")
# DSPath <- filter(DecompPath, Architecture == "DS")
# DecompPathA <- filter(DecompPath, Assignment_type == "Amateur")
# 
# LPPath100 <- ggplot(LPPath)+#, color = as.factor(Run))))+ #+  #Initalizes Colors Plot with Color Data 
#   geom_line((aes(x = stroke, y = Lie_100, group = as.factor(Run))),alpha = .25) +
#   facet_grid(rows = vars(Assignment_type),cols = vars(Rule)) + #plots faded color lines (Change alpha = .25 lighten/darken)
#   xlim(1,10)+
#   labs(x = "Number of strokes",
#        y = "Path to hole",
#        title = "LP Architecture: Top 1% Runs")+
#   #geom_hline(aes(yintercept = FairwayTransition, color = 'blue'))+
#   geom_hline(aes(yintercept = GreenTransition, color = 'green'))+
#   scale_y_continuous(trans='sqrt')+
#   theme(legend.position = "none") #removes legend
# 
# LPPath100
# 
# DSPath100 <- ggplot(DSPath)+#, color = as.factor(Run))))+ #+  #Initalizes Colors Plot with Color Data 
#   geom_line((aes(x = stroke, y = Lie_100, group = as.factor(Run))),alpha = .25) +
#   facet_grid(rows = vars(Assignment_type),cols = vars(Rule)) + #plots faded color lines (Change alpha = .25 lighten/darken)
#   xlim(1,10)+
#   labs(x = "Number of strokes",
#        y = "Path to hole",
#        title = "DS Architecture: Top 1% Runs")+
#   geom_hline(aes(yintercept = FairwayTransition, color = 'blue'))+
#   #geom_hline(aes(yintercept = GreenTransition, color = 'green'))+
#   scale_y_continuous(trans='sqrt')+
#   theme(legend.position = "none") #removes legend
# 
# DSPath100
# 
# HPath100 <- ggplot(HPath)+#, color = as.factor(Run))))+ #+  #Initalizes Colors Plot with Color Data 
#   geom_line((aes(x = stroke, y = Lie_100, group = as.factor(Run))),alpha = .25) +
#   facet_grid(rows = vars(Assignment_type),cols = vars(Rule)) + #plots faded color lines (Change alpha = .25 lighten/darken)
#   xlim(1,10)+
#   labs(x = "Number of strokes",
#        y = "Path to hole",
#        title = "H Architecture: Top 1% Runs")+
#   #geom_hline(aes(yintercept = FairwayTransition, color = 'blue'))+
#   #geom_hline(aes(yintercept = GreenTransition, color = 'green'))+
#   scale_y_continuous(trans='sqrt')+
#   theme(legend.position = "none") #removes legend
# 
# HPath100
# 
# RPath100 <- ggplot(RPath)+#, color = as.factor(Run))))+ #+  #Initalizes Colors Plot with Color Data 
#   geom_line((aes(x = stroke, y = Lie_100, group = as.factor(Run))),alpha = .25) +
#   facet_grid(rows = vars(Assignment_type),cols = vars(Rule)) + #plots faded color lines (Change alpha = .25 lighten/darken)
#   xlim(1,10)+
#   labs(x = "Number of strokes",
#        y = "Path to hole",
#        title = "R Architecture: Top 1% Runs")+
#   #geom_hline(aes(yintercept = FairwayTransition, color = 'blue'))+
#   #geom_hline(aes(yintercept = GreenTransition, color = 'green'))+
#   scale_y_continuous(trans='sqrt')+
#   theme(legend.position = "none") #removes legend
# 
# RPath100
# 
# ##################################
# # 2a Affect of multiple selection
# 
# Plot2aData <- filter(sumstatsDecomp, (Assignment == "AA"&Rule =="Optimal")|(Assignment == "PP"&Rule =="Optimal")|Architecture == "H"|Architecture =="R")
# Plot2aData$Tournament_type <- rep(c(1,10,100),8)
# 
# Plot2a <- ggplot(Plot2aData,aes(x = Tournament_type, y = Score,  color = Architecture))+
#   geom_errorbar(aes(ymin=Score-ci, ymax=Score+ci), width=.05)+#,                    # Width of the error bars
#   #stat_smooth(aes(x = Tournament_type, y = Score, linetype = "Exploential Fit"))
#   geom_line(aes(group =Architecture))+
#   geom_point(size = 2)+
#   facet_grid(rows = vars(Assignment_type),scales = "free")+
#   scale_x_continuous(trans='log10')
# Plot2a

















#########################
# Extra
#########################3


# ########################################
# # Plotting path
# 
DecompRule10 <- filter(DecompPath,Tournament_type=='Ten'&(Architecture == 'DS'|Architecture == 'LP'))
DecompRule1 <- filter(DecompPath,Tournament_type=='One'&(Architecture == 'DS'|Architecture == 'LP'))
H <- filter(DecompPath,Architecture == 'H')#&Tournament_type==Ten)
LP <- filter(DecompPath,Architecture == 'LP')#&Tournament_type==Ten)

HPath10 <- ggplot(H,(aes(x = stroke, y = Lie_100, group = as.factor(Run))))+#, color = as.factor(Run))))+ #+  #Initalizes Colors Plot with Color Data
  geom_line(alpha = .25) +
  #facet_grid(rows = vars(Tournament_type))+#,rows = vars(Architecture)) + #plots faded color lines (Change alpha = .25 lighten/darken)
  xlim(1,10)+
  labs(x = "Number of strokes",
       y = "Path to hole",
       title = "Whole Hole Architecture")+
  geom_hline(aes(yintercept = FairwayTransition, color = 'blue'))+
  geom_hline(aes(yintercept = GreenTransition, color = 'green'))+
  scale_y_continuous(trans='sqrt')+
  theme(legend.position = "none") #removes legend

HPath10
# 
# LPDSPath10 <- ggplot(DecompRule10,(aes(x = Stroke, y = Lie, group = as.factor(Run))))+#, color = as.factor(Run))))+ #+  #Initalizes Colors Plot with Color Data 
#   geom_line(alpha = .25) +
#   facet_grid(cols = vars(Architecture),rows = vars(Rule)) + #plots faded color lines (Change alpha = .25 lighten/darken)
#   xlim(1,10)+
#   labs(x = "Number of strokes",
#        y = "Path to hole",
#        title = "Impact of Modules and Interfaces")+
#   geom_hline(aes(yintercept = FairwayTransition, color = "blue"))+
#   geom_hline(aes(yintercept = GreenTransition, color = "green"))+
#   scale_y_continuous(trans='sqrt')+
#   theme(legend.position = "none") #removes legend
# 
# LPDSPath10
# 
# LPDSPath1 <- ggplot(DecompRule1,(aes(x = Stroke, y = Lie, group = as.factor(Run))))+#, color = as.factor(Run))))+ #+  #Initalizes Colors Plot with Color Data 
#   geom_line(alpha = .25) +
#   facet_grid(cols = vars(Architecture),rows = vars(Rule)) + #plots faded color lines (Change alpha = .25 lighten/darken)
#   xlim(1,10)+
#   labs(x = "Number of strokes",
#        y = "Path to hole",
#        title = "Impact of Modules and Interfaces")+
#   geom_hline(aes(yintercept = FairwayTransition, color = "blue"))+
#   geom_hline(aes(yintercept = GreenTransition, color = "green"))+
#   scale_y_continuous(trans='sqrt')+
#   theme(legend.position = "none") #removes legend
# 
# LPDSPath1
# 
# ##############################
# # Plot strokes
# 
# 
# strokesvscost <- ggplot(DecompStrokes)+
#   geom_point(aes(x=cost,y=Score,color = Assignment))+
#   facet_grid(cols = vars(Rule), rows = vars(Tournament_type), scales = "free")#+
# #facet_wrap(~Assignment_type, ncol=2)
# 
# strokesvscost
# 
# DecompStrokes10 <- filter(DecompStrokes, Tournament_type == "Ten")
# 
# strokes <- ggplot(DecompStrokes10)+
#   geom_boxplot(aes(x=Rule,y=Score, color = cost))+
#   facet_grid(rows = vars(Assignment_type), cols = vars(Architecture), scales = "free", space = "free")#+
# #facet_wrap(~Assignment_type, ncol=2)
# 
# strokes
# 
# #######################3
# #6. Is the performance improvement worth the cost?
# 
# 
# 
# #sumstatsDecomp
# Test6 <- filter(sumstatsDecomp, Tournament_type == "One"|Tournament_type == "Ten")
# 
# # Use 95% confidence intervals instead of SEM
# Test6plot <- ggplot(Test6) + 
#   geom_errorbar(aes(x = cost, y = Score, ymin=Score-ci, ymax=Score+ci),
#                 width=.2,                    # Width of the error bars
#                 position=position_dodge(.9))+
#   geom_point(aes(x=cost, y=Score, 
#                  shape=Architecture, 
#                  color = Tournament_type,
#                  size=2 ))+#position=position_dodge(), stat="identity") +
#   facet_grid(cols = vars(Assignment_type),scales = "free")
# 
# Test6plot
# 
# Test6bplot <- ggplot(Test6) + 
#   geom_errorbar(aes(x = cost, y = sched_part, ymin=sched_part-ci_sp, ymax=sched_part+ci_sp),
#                 width=.2,                    # Width of the error bars
#                 position=position_dodge(.9))+
#   geom_point(aes(x=cost, y=sched_part, 
#                  shape=Architecture, 
#                  color = Tournament_type,
#                  size=2 ))+#position=position_dodge(), stat="identity") +
#   facet_grid(cols = vars(Assignment_type),scales = "free")
# 
# Test6bplot
# 
