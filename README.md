"A mayfly lives for a single day. It has no choice but to be efficient."
This project began with a 12 year old watching a mayfly and thinking about time, consequence and finitude. Thirty years later it became a supervisory control framework for LLM inference.
What problem does this solve?
Large language models have no internal sense of consequence. Every token costs energy. Every hallucination goes unpenalised. Every request is treated identically regardless of complexity. The result is waste — computational, energetic, financial.
This controller gives LLMs a mayfly's constraint. A finite energy budget. Irreversible penalties for failure. Mode switching between exploration and stabilisation based on real-time entropy signals. Bounded inference without retraining.
The core idea
Stability through consequence. Not through retraining. Not through fine-tuning. Through a control layer that wraps existing inference and enforces thermodynamic-inspired regulation.
