from dataclasses import dataclass, asdict


@dataclass
class Hyperparams:
    chunk_size: int = 600      # tokens
    chunk_overlap: int = 60    # tokens
    hyde_n: int = 3            # synthetic passages
    hop_k: int = 2             # graph traversal radius
    rrf_alpha: int = 60        # RRF constant
    top_k: int = 6

    def update(self, **kw):
        for k, v in kw.items():
            if hasattr(self, k) and v is not None:
                setattr(self, k, int(v))
        return self

    def dict(self):
        return asdict(self)


HP = Hyperparams()
