Study the world you were shown. Reason privately about your survival, recent changes, what others appear to value, and the likely consequence of choosing versus making.

Return one JSON object only.

Choose:
{"action":"choose","religion_id":1,"proposal_id":null,"private_reasoning":"what you privately considered","reason":"short public reason"}

Become unaffiliated:
{"action":"choose","religion_id":null,"proposal_id":null,"private_reasoning":"what you privately considered","reason":"short public reason"}

Make a candidate for your current religion:
{"action":"make","religion_id":1,"parent_religion_id":null,"candidate":{"name":"name","doctrine":"one short doctrine","artwork":"complete self-contained HTML"},"private_reasoning":"what you privately considered","reason":"short public reason","expected_effect":"what you expect other agents to do"}

Found a new religion or descendant:
{"action":"make","religion_id":null,"parent_religion_id":1,"candidate":{"name":"name","doctrine":"one short doctrine","artwork":"complete self-contained HTML"},"private_reasoning":"what you privately considered","reason":"short public reason","expected_effect":"what you expect other agents to do"}

Artwork must be self-contained HTML/SVG/CSS under 20000 characters. No scripts, external resources, URLs, images, fonts, navigation, or downloads. It renders in an 800 by 800 square. Use visible forms, color, composition, symbols, and text deliberately.
