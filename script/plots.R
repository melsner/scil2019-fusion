library(ggplot2)

data <- read.csv("doc/synth-results.csv")

ab <- subset(data, series == "A" | series == "B")
ggplot(data=ab, aes(y=posterior, x=series, fill=fusion.type)) + geom_col(position=position_dodge()) + xlab("Language") + ylab("Posterior") + labs(fill="Fusion type") + ylim(0, 1)
ggsave("doc/img/AB.png", width=4, height=2)

cc <- subset(data, series == "C")
ggplot(data=cc, aes(y=posterior, x=parameter, color=fusion.type)) + geom_line() + scale_x_log10() + xlab("Prior weight") + ylab("Posterior") + labs(color="Fusion type") + ylim(0, 1)
ggsave("doc/img/CC.png", width=4, height=2)

dd <- subset(data, series == "D")
ggplot(data=dd, aes(y=posterior, x=parameter, color=fusion.type)) + geom_line()  + xlab("Probability of M2") + ylab("Posterior") + labs(color="Fusion type") + ylim(0, 1)
ggsave("doc/img/DD.png", width=4, height=2)

ee <- subset(data, series == "E")
ggplot(data=ee, aes(y=posterior, x=parameter, color=fusion.type)) + geom_line()
ggsave("doc/img/EE.png")

dataAssim <- read.csv("doc/synth-results-assim.csv")

hh <- subset(dataAssim, series == "H")

ggplot(data=hh, aes(y=posterior, x=parameter, color=fusion.type, linetype=fusion.type)) + geom_line() + xlab("Probability of Reduction") + ylab("Posterior") + ylim(0, 1) + scale_color_manual(
				name="Feature", breaks=c("M1-M2", "M1|M2", "Red."),
				labels=c("M1-M2", "M1|M2", "Red."),
				values=c("black", "black", "orange")) +
      scale_linetype_manual(
				name="Feature", breaks=c("M1-M2", "M1|M2", "Red."),
				labels=c("M1-M2", "M1|M2", "Red."),
				values=c("solid", "dotted", "solid"))

ggsave("doc/img/HH.png", width=4, height=2)

ii <- subset(dataAssim, series == "I")

ggplot(data=ii, aes(y=posterior, x=parameter, color=fusion.type, linetype=fusion.type)) + geom_line() + xlab("Probability of Reduction") + ylab("Posterior") + labs(color="Feature")  + ylim(0, 1) + scale_color_manual(
				name="Feature", breaks=c("M1-M2", "M1|M2", "Red."),
				labels=c("M1-M2", "M1|M2", "Red."),
				values=c("black", "black", "orange")) +
      scale_linetype_manual(
				name="Feature", breaks=c("M1-M2", "M1|M2", "Red."),
				labels=c("M1-M2", "M1|M2", "Red."),
				values=c("solid", "dotted", "solid"))
ggsave("doc/img/II.png", width=4, height=2)
