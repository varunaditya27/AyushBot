ayushbot/
│
├── firmware/
│   ├── sensor_pack/
│   │   ├── src/
│   │   │   ├── main.cpp              ← Arduino entry point
│   │   │   ├── sensors/
│   │   │   │   ├── max30100.cpp      ← SpO2 + HR driver
│   │   │   │   ├── ds18b20.cpp       ← Temperature driver
│   │   │   │   └── hx711.cpp         ← Weight/load cell driver
│   │   │   ├── fusion/
│   │   │   │   └── kalman.cpp        ← Multi-sensor Kalman filter
│   │   │   ├── tinyml/
│   │   │   │   ├── model.h           ← TFLite Micro model (INT8 .h file)
│   │   │   │   └── inference.cpp     ← TinyML pre-triage danger classifier
│   │   │   ├── comms/
│   │   │   │   ├── ble_gatt.cpp      ← BLE GATT service + characteristics
│   │   │   │   └── ascon_crypto.cpp  ← ASCON-128 lightweight encryption
│   │   │   └── config.h              ← Thresholds, pin definitions, constants
│   │   ├── platformio.ini            ← PlatformIO build config
│   │   └── README.md
│   └── edge_impulse/
│       ├── training_data/            ← Raw labeled CSV (SpO2, HR, Temp → label)
│       ├── export/                   ← Edge Impulse exported Arduino library
│       └── model_card.md             ← TinyML model accuracy, size, latency stats
│
├── android/                      ← Native Kotlin app (or Flutter)
│      ├── app/src/main/
│      │   ├── java/com/ayushbot/
│      │   │   ├── ui/               ← Screens: Patient, Vitals, Symptoms, Response
│      │   │   ├── ble/              ← BLE manager + GATT client
│      │   │   ├── mqtt/             ← MQTT client (Paho)
│      │   │   ├── db/               ← Room SQLite local database
│      │   │   ├── sync/             ← Background sync manager
│      │   │   └── tts/              ← AI4Bharat TTS integration
│      │   └── res/                  ← Layouts, drawables, strings (multilingual)
│      └── build.gradle
│
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py           ← LangGraph / state machine agent router
│   │   ├── agent_intake.py           ← Agent 1: Pre-triage + signal validation
│   │   ├── agent_diagnosis.py        ← Agent 2: Differential Dx + RAG retrieval
│   │   ├── agent_referral.py         ← Agent 3: Referral planning + Dijkstra routing
│   │   ├── agent_fl_sync.py          ← Agent 4: FL local training + gradient sync
│   │   ├── agent_language.py         ← Agent 5: IndicTrans2 + AI4Bharat TTS
│   │   └── schemas/
│   │       ├── patient_assessment.py ← Pydantic schema: structured input
│   │       ├── differential.py       ← Pydantic schema: diagnosis output
│   │       └── action_plan.py        ← Pydantic schema: referral + drug plan
│   │
│   ├── rag/
│   │   ├── pipeline/
│   │   │   ├── chunker.py            ← Section-aware PDF chunker (400-600 tokens)
│   │   │   ├── embedder.py           ← all-MiniLM-L6-v2 / BioLORD embedder
│   │   │   ├── indexer.py            ← HNSW index builder (FAISS + PQ compression)
│   │   │   ├── retriever.py          ← Top-k HNSW retrieval
│   │   │   └── reranker.py           ← Cross-encoder reranker (ms-marco-MiniLM)
│   │   ├── index/
│   │   │   ├── ayushbot.faiss        ← Compiled HNSW FAISS index (binary)
│   │   │   ├── ayushbot_meta.json    ← Chunk metadata (source, page, ICD codes)
│   │   │   └── ayushbot_pq.faiss     ← PQ-compressed index (for phone deployment)
│   │   └── build_index.py            ← One-shot script: corpus → FAISS index
│   │
│   ├── llm/
│   │   ├── loader.py                 ← Load quantized Phi-3 Mini / Gemma-3 1B
│   │   ├── inference.py              ← LLM inference wrapper + streaming
│   │   └── prompts/
│   │       ├── system_prompt.txt
│   │       ├── diagnosis_prompt.j2   ← Jinja2 template: diagnosis agent
│   │       └── referral_prompt.j2    ← Jinja2 template: referral agent
│   │
│   ├── fl/
│   │   ├── local_trainer.py          ← Local SGD fine-tuning (5 epochs per round)
│   │   ├── dp_mechanism.py           ← Gradient clipping + Gaussian DP noise
│   │   ├── aggregator.py             ← FedAvg + Krum Byzantine-robust variant
│   │   ├── gossip.py                 ← Gossip P2P FL fallback (no central server)
│   │   └── sync_client.py            ← DTN-style store-carry-forward QUIC sync
│   │
│   ├── security/
│   │   ├── mqtt_broker_config/       ← Mosquitto TLS 1.3 + mTLS config files
│   │   ├── certs/                    ← CA, server, client certificates (gitignored)
│   │   └── auth.py                   ← JWT token validation for ASHA device auth
│   │
│   ├── api/
│   │   ├── main.py                   ← FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── triage.py             ← POST /triage — main inference endpoint
│   │   │   ├── sync.py               ← POST /fl/sync — gradient upload/download
│   │   │   └── health.py             ← GET /health — gateway status check
│   │   └── middleware/
│   │       └── rate_limiter.py
│   │
│   ├── db/
│   │   ├── models.py                 ← SQLAlchemy models (Case, Patient, FLRound)
│   │   ├── session.py                ← SQLite engine + session factory
│   │   └── migrations/               ← Alembic migration scripts
│   │
│   ├── config.yaml                   ← Gateway-level config (model paths, thresholds)
│   ├── Dockerfile
│   └── requirements.txt
│
├── cloud/
│   ├── fl_server/
│   │   ├── server.py                 ← Flower FL global aggregation server
│   │   ├── strategy.py               ← FedAvg / FedProx / SCAFFOLD strategy impl.
│   │   └── model_registry.py         ← Model versioning + changelog
│   ├── analytics/
│   │   ├── dashboard/                ← Streamlit or Grafana dashboard
│   │   │   ├── app.py
│   │   │   └── charts/
│   │   └── aggregator.py             ← Population-level anonymized analytics
│   ├── api/
│   │   └── main.py                   ← Cloud REST API (model push/pull, analytics)
│   ├── Dockerfile
│   └── requirements.txt
│
├── ml/
│   ├── triage_classifier/
│   │   ├── 01_extract_mimiciv.py     ← MIMIC-IV cohort extraction (SQL → CSV)
│   │   ├── 02_process_nfhs5.py       ← NFHS-5 feature engineering
│   │   ├── 03_pretrain.py            ← XGBoost pre-training on MIMIC-IV
│   │   ├── 04_finetune_india.py      ← Fine-tuning on NFHS-5 derived dataset
│   │   ├── 05_quantize.py            ← INT8 quantization for TinyML export
│   │   └── model_card.md
│   ├── fl_simulation/
│   │   ├── simulate_nodes.py         ← Create 5-10 virtual ASHA nodes from NFHS-5
│   │   ├── run_fedavg.py             ← Run FedAvg simulation, log convergence
│   │   ├── run_fedprox.py
│   │   ├── run_scaffold.py
│   │   ├── run_byzantine.py          ← Byzantine attack simulation + Krum defense
│   │   └── run_gossip.py             ← Gossip FL simulation
│   ├── language_agent/
│   │   ├── train_intent.py           ← Fine-tune IndicBERT on IHQID intent task
│   │   ├── train_ner.py              ← Fine-tune IndicBERT on IHQID entity task
│   │   └── eval_indic.py             ← Evaluate F1 per language per intent class
│   ├── signal_quality/
│   │   ├── train_motion_filter.py    ← ScientISST MOVE → motion artifact model
│   │   └── eval_hr_accuracy.py       ← BIG IDEAs + Stress dataset → HR eval
│   └── notebooks/
│       ├── eda_mimiciv.ipynb
│       ├── eda_nfhs5.ipynb
│       ├── fl_convergence_plots.ipynb
│       └── rag_eval.ipynb
│
├── data/
│   ├── raw/                          ← NEVER committed to git (.gitignore)
│   │   ├── mimiciv/                  ← MIMIC-IV downloaded files
│   │   ├── nfhs5/                    ← NFHS-5 downloaded .dta files
│   │   └── physionet_wearable/       ← PhysioNet wearable datasets
│   ├── processed/                    ← Derived, anonymized — safe to share
│   │   ├── triage_train.csv
│   │   ├── triage_test.csv
│   │   ├── fl_node_splits/           ← Per-node dataset JSONs (anonymized)
│   │   └── ihqid_processed/          ← Cleaned IHQID train/test splits
│   ├── corpus/
│   │   ├── raw_pdfs/                 ← MoHFW, WHO IMCI, NHM modules (PDFs)
│   │   ├── cleaned_text/             ← Extracted + cleaned text (.txt per doc)
│   │   └── chunks/                   ← Final chunks as JSONL (id, text, metadata)
│   └── synthetic/
│       ├── health_gym_sepsis.csv
│       ├── health_gym_hypotension.csv
│       └── generated_cases/          ← Scripted test case scenarios (20-30 cases)
│
├── infra/
│   ├── docker/
│   │   ├── gateway.Dockerfile
│   │   ├── cloud.Dockerfile
│   │   └── nginx.conf                ← Reverse proxy for gateway services
│   ├── docker-compose.yml            ← Full local simulation stack
│   ├── docker-compose.prod.yml       ← Production (RPi 4 + VPS)
│   ├── rpi_setup.sh                  ← One-shot RPi 4 provisioning script
│   ├── mosquitto/
│   │   ├── mosquitto.conf
│   │   └── acl.conf                  ← MQTT topic access control list
│   └── monitoring/
│       ├── prometheus.yml
│       └── grafana_dashboard.json
│
├── research/
│   ├── paper/
│   │   ├── main.tex                  ← Full LaTeX paper
│   │   ├── figures/                  ← All TikZ/PGF figures + exported plots
│   │   ├── bibliography.bib          ← BibTeX references
│   │   └── acl_latex.sty             ← Style file for target venue
│   ├── experiments/
│   │   ├── exp1_edgerag_latency/     ← RQ1: TTFT + recall@k results
│   │   ├── exp2_multiagent_accuracy/ ← RQ2: Dx accuracy vs baselines
│   │   ├── exp3_fl_convergence/      ← RQ3: FL convergence + privacy budget
│   │   ├── exp4_tinyml_benchmark/    ← TinyML accuracy + latency on Arduino
│   │   └── exp5_security_bench/      ← ASCON vs AES vs TLS benchmark
│   └── results/
│       ├── tables/                   ← CSV exports of all result tables
│       └── plots/                    ← PDF/PNG of all paper figures
│
├── tests/
│   ├── unit/
│   │   ├── test_agents.py
│   │   ├── test_rag_pipeline.py
│   │   ├── test_fl_aggregator.py
│   │   └── test_dp_mechanism.py
│   ├── integration/
│   │   ├── test_full_pipeline.py     ← End-to-end: vitals in → action plan out
│   │   └── test_ble_mqtt_stack.py
│   └── simulation/
│       └── run_asha_scenario.py      ← 20-case scripted ASHA visit simulation
│
└── docs/
    ├── architecture.md               ← 5-layer architecture explanation
    ├── api_reference.md              ← FastAPI auto-docs supplement
    ├── setup_guide.md                ← Full dev environment setup
    ├── rpi_deployment.md             ← PHC gateway deployment guide
    ├── dataset_guide.md              ← How to download + prepare all datasets
    └── diagrams/
        ├── system_architecture.drawio
        ├── agent_flow.drawio
        └── fl_protocol.drawio
