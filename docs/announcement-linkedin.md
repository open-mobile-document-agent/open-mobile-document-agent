# LinkedIn announcement (draft)

Your phone will soon read every document you photograph. That part is solved.

What isn't solved: what that document actually proves.

Which number came from where on the page? Did a check digit confirm it, or did a model guess? Did you approve it? And when an app, an assistant or a hotel asks for it — can you share "over 18" instead of your passport?

Today I'm publishing OMDA — the Open Mobile Document Agent specification, v0.1.

→ Every fact carries its evidence: value, quote, region, page hash
→ AI proposes; deterministic checks or the owner confirm (Verhoeff, Luhn, ICAO 9303 MRZ, ePassport chips)
→ Runs on the device, encrypted with hardware keys, portable between apps
→ One agent interface: MCP, Android AppFunctions, iOS App Intents
→ Share proof, not documents: selective disclosure over W3C Verifiable Credentials 2.0 + SD-JWT
→ Disclose, don't prohibit: every gap is labelled, never hidden

Spec, JSON Schemas, registries, examples and reference tools are open under Apache-2.0:
https://github.com/open-mobile-document-agent/open-mobile-document-agent

Feedback and implementers welcome.

#OpenSource #OnDeviceAI #DocumentAI #VerifiableCredentials #MCP #Android #Privacy
