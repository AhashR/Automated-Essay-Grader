Learning Story: Begin maken aan de lokale AI Agent & Google Cloud AI Agent
Leerdoelen
Lokale AI agent opzetten
Als student wil ik leren hoe ik een lokale AI agent opzet met Ollama, zodat ik zonder cloudkosten kan experimenteren met een LLM-gebaseerde feedbackagent.
Google Cloud AI agent configureren
Als student wil ik leren hoe ik een AI agent opzet via Google Cloud SQL for PostgreSQL, zodat ik een schaalbare cloudoplossing kan vergelijken met de lokale aanpak.
Technisch ontwerp van de feedbackagent
Als student wil ik een technisch ontwerp maken van de feedbackagent, zodat ik de architectuur, componenten en dataflow vastleg voordat ik begin met implementeren.
Trainingsdata verzamelen en labelen
Als student wil ik voorbeeld learning stories opvragen en deze labelen als "goed" of "slecht", zodat ik een gelabelde dataset heb waarmee het model kan leren onderscheiden.
Classificatiemodel of prompt-engineering toepassen
Als student wil ik leren hoe ik een AI model via few-shot prompting of fine-tuning kan inzetten voor classificatie, zodat de agent zelfstandig beoordeelt of een learning story aan de kwaliteitscriteria voldoet.
Manier van leren
Actiepunten
10-20 geanonimiseerde voorbeeld learning stories aanvragen (mix van goed en slecht)
Labelschema opstellen: wat maakt een learning story "goed"? (bijv. concreet leerdoel, koppeling aan competentie, reflectie aanwezig)
Architectuurdiagram tekenen: welke componenten heeft de agent (LLM, database, API, input/output flow)?
Dataflow uitwerken: hoe stroomt een learning story door het systeem van input naar feedbackoutput?
Technisch ontwerpdocument opstellen met motivatie voor componentkeuzes (Ollama lokaal vs. Gemini via Cloud SQL)
Ollama lokaal installeren en een model draaien met de voorbeeld learning stories
Google Cloud project aanmaken en Gemini API key configureren
Eerste prompt engineering iteratie uitvoeren met de verzamelde voorbeelden
Koppeling aan competenties
Deze learning story bewijst groei op de volgende competenties:
Ontwerpen
Een architectuurdiagram en technisch ontwerpdocument opstellen van de feedbackagent: welk model, welke data-opslag (PostgreSQL), welke classificatielogica en hoe de dataflow verloopt van input naar feedbackoutput.
Realiseren
De lokale Ollama agent en de Google Cloud agent implementeren en koppelen aan een gelabelde dataset van learning stories.

| Leerdoel | Aanpak | Bron/Tool |
| --- | --- | --- |
| Lokale AI agent | Ollama installeren, model draaien, Python-integratie via ollama library | Ollama docs, LangChain |
| Google Cloud AI agent | Cloud SQL for PostgreSQL configureren in de Google Cloud Console | Google Cloud documentatie |
| Technisch ontwerp | Architectuurdiagram tekenen met componenten (LLM, PostgreSQL, Python backend, input/output flow), vastleggen in een technisch ontwerpdocument | Draw.io |
| Trainingsdata verzamelen | Voorbeeld learning stories opvragen bij docent, handmatig labelen (goed/slecht) met motivatie | Docent + eigen beoordeling |
| Classificatie logica | Few-shot prompting met gelabelde voorbeelden, evalueren op nieuwe stories | OpenAI / Gemini API prompting guides |
