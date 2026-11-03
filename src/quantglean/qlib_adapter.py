"""Optional public Qlib DatasetH/LinearModel adapter; no providers or downloaded data."""
from __future__ import annotations
import importlib.metadata
import numpy as np
import pandas as pd

def fit_predict(train_x: pd.DataFrame, train_y: pd.Series, predict_x: pd.DataFrame, alpha: float):
    try:
        version = importlib.metadata.version("pyqlib")
    except importlib.metadata.PackageNotFoundError as exc:
        raise ImportError('Install the optional backend: python -m pip install -e ".[qlib]"') from exc
    if version != "0.9.7":
        raise ValueError("This adapter is verified with pyqlib==0.9.7; review compatibility before changing versions")
    if train_x.index.get_level_values("date").max() >= predict_x.index.get_level_values("date").min():
        raise ValueError("Qlib training and inference date ranges must not overlap")
    from qlib.data.dataset import DatasetH
    from qlib.data.dataset.handler import DataHandlerLP
    from qlib.data.dataset.loader import StaticDataLoader
    from qlib.contrib.model.linear import LinearModel
    features = pd.concat([train_x, predict_x]).copy()
    # Qlib expects naive datetime/instrument indexing. No label from inference is supplied.
    dates = features.index.get_level_values("date").tz_localize(None)
    features.index = pd.MultiIndex.from_arrays([dates, features.index.get_level_values("instrument")],
                                               names=["datetime", "instrument"])
    labels = pd.Series(np.nan, index=features.index, name="target")
    labels.iloc[:len(train_x)] = train_y.to_numpy()
    combined = pd.concat({"feature": features, "label": labels.to_frame()}, axis=1).sort_index()
    train_dates = train_x.index.get_level_values("date").tz_localize(None)
    inference_dates = predict_x.index.get_level_values("date").tz_localize(None)
    handler = DataHandlerLP(data_loader=StaticDataLoader(combined), infer_processors=[], learn_processors=[])
    dataset = DatasetH(handler=handler, segments={"train": (train_dates.min(), train_dates.max()),
                                                   "inference": (inference_dates.min(), inference_dates.max())})
    model = LinearModel(estimator="ridge", alpha=alpha, fit_intercept=True, include_valid=False)
    model.fit(dataset)
    predicted = model.predict(dataset, segment="inference")
    # Restore our order explicitly rather than relying on provider sorting.
    expected = pd.MultiIndex.from_arrays([inference_dates, predict_x.index.get_level_values("instrument")],
                                         names=["datetime", "instrument"])
    values = predicted.reindex(expected).to_numpy()
    return values, np.asarray(model.coef_, dtype=float), float(model.intercept_), version
