# SOMA Shared

Shared contracts, database models, and utilities for SOMA projects.

## Installation

### From Git repository

```bash
pip install git+https://github.com/DendriteHQ/SOMA-shared.git
```

### From Git repository (specific branch)

```bash
pip install git+https://github.com/DendriteHQ/SOMA-shared.git@main
```

## Usage

### Contracts

```python
from soma_shared.contracts.common.envelopes import ResponseEnvelope, ErrorEnvelope
from soma_shared.contracts.miner.v1.messages import MinerMessage
from soma_shared.contracts.validator.v1.messages import ValidatorMessage
```

### Database Models

```python
from soma_shared.db.models.miner import Miner
from soma_shared.db.models.validator import Validator
from soma_shared.db.session import get_db_session
```

### Utilities

```python
from soma_shared.utils.signer import sign_message
from soma_shared.utils.verifier import verify_signature
from soma_shared.utils.nonce_cache import NonceCache
```

## Structure

```
SOMA-shared/
├── contracts/          # API contracts and message definitions
│   ├── admin/         # Admin-related contracts
│   ├── api/           # Public API contracts
│   ├── common/        # Common envelopes and signatures
│   ├── miner/         # Miner-specific contracts
│   └── validator/     # Validator-specific contracts
├── db/                # Database models and utilities
│   ├── models/        # SQLAlchemy ORM models
│   └── repositories/  # Database repositories
└── utils/             # Utility functions
    ├── signer.py      # Message signing utilities
    ├── verifier.py    # Signature verification
    └── nonce_cache.py # Nonce management
```

## License

MIT
