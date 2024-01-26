# Testing calling r from python
msgman <- function(msg="") {
  list(msg = paste0("The message is: '", msg, "'"))
}

msgman("desired message")