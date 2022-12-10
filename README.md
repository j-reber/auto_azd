# How to use Auto AZD
* The main parameters can be set in the main method. Care for proper parameters
* You can set a custom signature. 
Therefore change the picture in the signature folder
* If this feature is not wanted, just comment the line to #can.drawimage...
* If you set a custom signature the picture should have a transparent background
* Custom picture might need to be set manually on the pdf just change the ints in
can.drawImage("signature/signature_transparent.png", 110, 170, width=160, height=60, mask="auto")
to values that fit. Also, the height and width of the pictures can be adjusted with the respective 
values