# Field Configuration (config/fields.json)

## Purpose
A single JSON file defines allowed fields, their validation rules, allowed outputs, and prompt snippets for the LLM. The backend loads this file and builds prompts/messages dynamically.

## Schema
```json
{
  "system_prompt": "string (base system instruction)",
  "fields": [
    {
      "name": "string",
      "description": "string",
      "allowed_status": ["success", "objection"],
      "allowed_terms": ["..."],              // used for valid3 classification
      "prompt": "string with validation guidance",
      "example_context": "string (optional)"
    }
  ]
}
```

## Current fields
- `valid1`: exactly 11 digits (0-9).
- `valid2`: letters only (A-Z + Polish diacritics), first letter uppercase.
- `valid3`: classify job/description into dentist or hairdresser; otherwise objection.
- `text`: generic text field.

## How to extend
1) Add a new entry under `fields` with name/description/prompt/allowed_status/allowed_terms.
2) If you add new classification terms, list them in `allowed_terms` so the validator can enforce success only for those terms.
3) Keep responses strict: backend expects `status` in {success, objection} and a non-empty `justification`.


