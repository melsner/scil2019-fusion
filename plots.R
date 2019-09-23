library(ggplot2)

data <- read.csv("doc/synth-results.csv")

ab <- subset(data, series == "A" | series == "B")
ggplot(data=ab, aes(y=posterior, x=series, fill=fusion.type)) + geom_col(position=position_dodge()) + xlab("Language") + ylab("Posterior") + labs(fill="Fusion type")
ggsave("doc/img/AB.png")

cc <- subset(data, series == "C")
ggplot(data=cc, aes(y=posterior, x=parameter, color=fusion.type)) + geom_line() + scale_x_log10() + xlab("Prior weight") + ylab("Posterior") + labs(fill="Fusion type")
ggsave("doc/img/CC.png")

dd <- subset(data, series == "D")
ggplot(data=dd, aes(y=posterior, x=parameter, color=fusion.type)) + geom_line()  + xlab("Probability of M2") + ylab("Posterior") + labs(fill="Fusion type")
ggsave("doc/img/DD.png")

ee <- subset(data, series == "E")
ggplot(data=ee, aes(y=posterior, x=parameter, color=fusion.type)) + geom_line()
ggsave("doc/img/EE.png")

dataAssim <- read.csv("doc/synth-results-assim.csv")

ggplot(data=dataAssim, aes(y=posterior, x=parameter, color=fusion.type) + geom_line() + xlab("Probability of Reduction") + ylab("Posterior") + labs(fill="Feature")
