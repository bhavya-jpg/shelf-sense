# Shelf-Sense demo video: narration script (final)

Voice: Chatterbox (Resemble AI, MIT), generated locally; checked back with Whisper. `say` is what the model was given (spelled for pronunciation); captions use the written form.


## 1. Hook  (00:00:00 – 00:00:06)

- Every store has a shelf that is quietly running low.
- And most shelves are still checked by eye.

## 2. The problem  (00:00:06 – 00:00:20)

- Someone walks the aisle, counts the boxes, and writes it down.
- Gaps sit unnoticed between walks, and two people can count the same shelf two different ways.
- Nobody knows what a missing facing actually costs.

## 3. The solution  (00:00:19 – 00:00:35)

- Shelf-Sense turns one shelf photograph into a preliminary compliance report.  
  _say:_ Shelf Sense turns one shelf photograph into a preliminary compliance report.
- Choose a shelf specification, add a photo, and run one inspection.
- A vision model counts each product, shelf by shelf. Code makes every decision.

## 4. Real demo  (00:00:34 – 00:00:49)

- This is the real application, inspecting a photo we took of a cereal bay.
- The photo goes to Gemma-4-31B-IT on AMD Developer Cloud's Token Factory.  
  _say:_ The photo goes to Gemma four, thirty one B, on A M D Developer Cloud's Token Factory.
- The shared endpoint takes a while to answer, so we have sped up the wait.

## 5. The result  (00:00:49 – 00:01:08)

- Here is the result: counts for every product, shelf by shelf, against the expected inventory.
- Discrepancies are flagged, and an estimated margin at risk is calculated in code.
- That figure is always labelled unverified. It comes from AI-estimated counts and demo margin assumptions.  
  _say:_ That figure is always labelled unverified. It comes from A I estimated counts and demo margin assumptions.

## 6. Actions  (00:01:08 – 00:01:17)

- Then a restocking list.
- The model can reword it, but every name, count and figure is inserted by code, and the app says who wrote it.

## 7. Architecture  (00:01:17 – 00:01:38)

- Under the hood it is one Python process.
- The photo is resized to 1024 pixels and sent with the specification in a single call.  
  _say:_ The photo is resized to ten twenty four pixels and sent with the specification in a single call.
- The model returns structured counts. They are validated, and anything unreliable goes to review.
- The verdict, the money, and the action list are computed in plain Python.

## 8. Evaluation  (00:01:37 – 00:02:00)

- We measured it against a shelf we counted by hand.
- A shelf-by-shelf prompt cut the counting error from eight boxes to one.  
  _say:_ A shelf by shelf prompt cut the counting error from eight boxes to one.
- But the model still misses one half-hidden Koko Krunch box, at 100% confidence. So this fully stocked shelf is reported as short.  
  _say:_ But the model still misses one half hidden Koko Krunch box, at one hundred percent confidence. So this fully stocked shelf is reported as short.
- So every figure is labelled unverified, and the per-shelf counts let a person check it in seconds.  
  _say:_ So every figure is labelled unverified, and the per shelf counts let a person check it in seconds.

## 9. Inference on AMD  (00:01:59 – 00:02:12)

- Every inspection runs on AMD, with a median of about 18 seconds on the shared endpoint.  
  _say:_ Every inspection runs on A M D, with a median of about eighteen seconds on the shared endpoint.
- For a store manager, it is a fast second opinion: where to look, and roughly what is at stake.

## 10. Close  (00:02:12 – 00:02:29)

- Next: better counting under occlusion, human verification of uncertain findings, and many more shelves.
- Shelf-Sense. AMD-hosted vision, decisions in code, honest about its limits.  
  _say:_ Shelf Sense. A M D hosted vision, decisions in code, honest about its limits.
