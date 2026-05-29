Plan:

Current State: A dictionary OCR , MDF parsing pipeline used to benchmark models,

Goal:

- To make this code-base into a proper python package, installable through pip, named the package MUDIDI.
- Add a benchmark mode (—benchmark), when passed it will perform what our current code does, requiring the stage-1 gold and stage-2 gold files.
- Create an inference pipeline that have the following feature, callable after installing package by simply calling `mudidi --{argument-1} --{argument-2}, etc` :
  1. Pass in previous and next page context for inference model, for benchmark it parses each pages independently since it’s not consecutive, for inference, we want to see the previous and next context as entry in the current page could overflow to the next. Ensure that output for stage-1 and stage-2 belongs to. For those cases (part of entries at the end of the pages overflow, or entries at the start of the pages belongs to the entries at previous pages), ensure that the stage1 and stage2-output only belongs to the current page (do not include the part of entry that belongs to previous page, but please include the entry that overflowed into the next)
  2. Add an option to run stage-1 and 2 seperately, or run both at the same time. Pass output of stage1 to 2 (currently stage 2 receives the gold ocr text , but that’s onyl for benchmark, for inference we want to pass the ocr output of stage-1)
  3. One of the key arguments is —output-dir, for the case of running the ‘all’ stage mode, then the output dir will contain stage-1, and stage-2 subdir by default.
  4. When calling this main cli it should accept the following (non exhaustive):
     1. path to alphabet list (.txt or markdown file)
     2. path to directory containing dictionary introduction (pdf, png, jpg, jpeg)
     3. path to dictionary pages snippet (pdf, png, jpg, jpeg)
  5. You should adjust the current prompts for stage 1` and 2 as they are made for benchmark (consider renaminig the current ones bya dding a benchmark suffix in the propmt vairiable name)
  6. Add proper test-suite to ensure every functionality works
