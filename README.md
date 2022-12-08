# MonkeyPox-Reddit-DSN

### Data Collection Scripts

Run  ```scripts/create_samples.py``` to collect discussions from Reddit and save data. Need your own Reddit client ID and secret which can be generated by creating a Reddit account and then going to https://www.reddit.com/prefs/apps/ and going through the steps to create a developed application with the "script" type when selecting the radio buttons.

### LDA Instructions/Requirements 
Install conda env before running LDA notebook:
`conda env create -f lda.yml`


### LIWC Instructions/Requirements
LIWC File requires/uses the LIWC_2015.dic file. This needs to be supplied by the user as a license must be purchased to acquire and use this file.
To run the work, you can just run the liwc script in ```scripts/liwc_analysis.py```
Some examples on how to run the various methods for calculating t-test, LIWC category word usage, and Kruskal-Wallis tests are present at the bottom of the file.
