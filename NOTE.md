# RFQ Parser: Note

## 1. Approach
A rule-based parser in plain Python (only `re` and `difflib`, so
requirements.txt is empty). Four parts:
- **Quantity and unit:** a regex finds every number with its multiplier
  (k, hazaar, lakh/lac, crore, "ek lakh") and the word after it. Each candidate
  gets a priority: count words (pcs, bags, nos) highest, kg lowest. Numbers
  followed by "capacity" or "bag" (fill weight) are skipped.
- **gsm / micron:** a number directly followed by gsm or mic/micron.
- **Category:** an ordered keyword list (jumbo -> fibc is checked before the
  generic "bag"), with fuzzy matching for typos.
- **Location:** cue words (to, at, delivery), Hinglish (X mein / X ke liye),
  a place-like comma segment, then the last non-filler word. A stop-word list
  stops product words being returned as a place. There is no fixed city list,
  so unseen cities work.

## 2. Score
my_tests.jsonl: [52]/[52] exact matches (category [52/52 ], quantity [52/52], unit [52/52],
gsm [ 52/52], micron [52/52], location [52/52]).
Caveat: I wrote the parser and these tests together, so this score is
optimistic. On 18 fresh messages I wrote after the parser was built, only
10 were fully correct on the first run; the failures became fixes and new tests.
score.py was not included in the assignment files, so I used my own script
(my_score.py) that compares every field exactly.

## 3. Three messages my parser gets wrong
1. "stretch film 17 mic 800 kg Pimpri Chinchwad" -> location "Chinchwad",
   expected "Pimpri Chinchwad". Without a city list, I only take a few
   words, and joining more would wrongly turn "good quality Surat"
   into "Quality Surat".
2. "need 3 lacs pcs poly mailer bags Noida" -> woven_sack. Poly mailers are not
   one of the 7 categories, and my generic "bag" fallback guesses instead of
   returning None.
3. "jumbo bags 750 kg 100 pieces Anand Gujarat" -> location "Gujarat",
   expected "Anand". Only one place is allowed, and the last one wins; the
   city/state difference needs real geography knowledge.

## 4. With 1,000 real labelled examples
- First I would run the parser on all 1,000 and see which field fails most.
  I would fix that group first instead of guessing.
- I would build the stop-word list and a list of Indian cities from real
  messages, so location is less guesswork.
- For category and location I would try a small ML model (for example a text
  classifier and a name-finding model) and compare it with the rules.
  I would keep rules for numbers (lakh, hazaar, kg vs pcs), because they
  already work and are easy to debug.
- I would split the data into a part for tuning and a part I never touch,
  so the score is honest.

## 5. How I would know it works with real buyers
- Every week, take a random sample of real messages, label them by hand and
  track accuracy for each of the six fields.
- Track how often fields come back empty (None) and which messages the
  parser could not read at all.
- Let the sales team correct wrong fields and save each correction.
  Corrections become new test examples and show what is breaking.
- Watch for new words and new cities appearing, since buyers change how
  they write.

## 6. Tools used
I used Claude (AI assistant) as a tutor: it explained regex step by step,
drafted most of the code, and wrote most of the test examples. I typed and
ran everything myself in VS Code, found and fixed bugs, and checked every
test label by hand.
Bugs I hit and fixed:
- On my own test set, 46/47 passed. The miss was "...Nagpur ke liye": the
  Hinglish location rule only knew "mein/me/tak". I added "ke liye/ko".
- First version took the first number as quantity, so "cement bags 25 kg,
  2000 bags" returned 25 kg. I changed it to a priority system.
- On fresh messages I wrote after building, "50 hajar" returned 50 and
  "ek lakh" returned None. I added those words.

Assumption: if a message has no quantity, I return quantity None, unit "pcs".