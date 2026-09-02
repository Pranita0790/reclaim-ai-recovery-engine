def __init__(self) -> None:
    backend_directory = Path(__file__).resolve().parents[2]

    model_path = (
        backend_directory
        / "models"
        / "recovery_probability_model.joblib"
    )

    if not model_path.exists():
        raise FileNotFoundError(
            f"ML model not found at: {model_path}"
        )

    loaded_artifact = joblib.load(model_path)

    if isinstance(loaded_artifact, dict):
        if "model" not in loaded_artifact:
            raise ValueError(
                "Saved ML artifact does not contain a 'model' key."
            )

        self.model = loaded_artifact["model"]

        self.feature_count = loaded_artifact.get(
            "feature_count",
            None,
        )
    else:
        self.model = loaded_artifact
        self.feature_count = None