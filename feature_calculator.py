import json

import numpy as np
import pandas as pd


class FeatureCalculator:
    """
    Physics feature engine for PHEA-Atlas.

    Every formula and column name here was cross-checked directly
    against:
      - element_properties_verified.csv (actual column names)
      - dHmix_lookup_matrix.npy + element_to_index.json
      - PHEA_Final_Model.pkl (booster.feature_names -> ground truth
        list of the 20 features the model actually expects, and the
        real split-value ranges used to validate each formula/unit)
    """

    # Exact feature list + order the trained model expects.
    # (Confirmed via model.get_booster().feature_names -- NOT from
    # v10_selected_features.csv, which is a stale intermediate file
    # that includes "delta_en", a feature the final model never used.)
    FEATURE_ORDER = [
        "Alloy_DeltaHmix_kJmol",
        "delta_radius",
        "std_atomic_radius_pm",
        "el1_idx",
        "mean_vec",
        "Omega",
        "el5_idx",
        "std_electronegativity",
        "Lambda",
        "std_melting_point_K",
        "el2_idx",
        "mean_density",
        "el4_idx",
        "mean_electronegativity",
        "std_atomic_mass",
        "mean_melting_point_K",
        "el3_idx",
        "mean_atomic_radius_pm",
        "std_density",
        "mean_atomic_mass",
    ]

    R = 8.314462618  # gas constant, J/mol.K

    def __init__(self):

        print("Loading Physics Engine...")

        # element_properties_verified.csv columns (verified):
        # element, atomic_number, atomic_weight, atomic_radius_pm,
        # electronegativity, melting_point_K, density, group, period,
        # atomic_mass, VEC, source_note
        self.props = pd.read_csv(
            "data/element_properties_verified.csv"
        )
        self.props = self.props.set_index("element")

        with open("data/element_to_index.json", "r") as f:
            self.element_index = json.load(f)

        self.lookup = np.load(
            "data/dHmix_lookup_matrix.npy"
        )

        print("Physics Engine Ready")

    # -----------------------------------------------------
    def get(self, element):
        return self.props.loc[element]

    # -----------------------------------------------------
    # Composition-weighted mean / std of any property
    # -----------------------------------------------------
    def mean_property(self, elements, compositions, column):
        value = 0.0
        for e, c in zip(elements, compositions):
            value += self.get(e)[column] * c / 100
        return value

    def std_property(self, elements, compositions, column):
        mean = self.mean_property(elements, compositions, column)
        s = 0.0
        for e, c in zip(elements, compositions):
            x = self.get(e)[column]
            s += (c / 100) * (x - mean) ** 2
        return np.sqrt(s)

    # -----------------------------------------------------
    # Alloy-level DeltaHmix from the precomputed lookup matrix
    # (regular-solution mixing rule: sum 4*xi*xj*Hij over all pairs)
    # -----------------------------------------------------
    def delta_hmix(self, elements, compositions):
        x = np.array(compositions) / 100
        n = len(elements)
        hmix = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                idx1 = self.element_index[elements[i]]
                idx2 = self.element_index[elements[j]]
                hmix += 4 * x[i] * x[j] * self.lookup[idx1, idx2]
        return hmix

    # -----------------------------------------------------
    # Hume-Rothery atomic size mismatch (delta), in PERCENT
    # -----------------------------------------------------
    def delta_radius(self, elements, compositions):
        c = np.array(compositions) / 100
        r = np.array([self.get(e)["atomic_radius_pm"] for e in elements])
        mean_r = np.sum(c * r)
        return np.sqrt(np.sum(c * (1 - r / mean_r) ** 2)) * 100

    # -----------------------------------------------------
    # Full mixing entropy (with R) -- used only inside Omega
    # -----------------------------------------------------
    def mixing_entropy_with_R(self, compositions):
        c = np.array(compositions) / 100
        c = c[c > 0]
        return -self.R * np.sum(c * np.log(c))

    # -----------------------------------------------------
    # Dimensionless entropy term (ln N for equiatomic) -- used
    # only inside Lambda. Confirmed against the trained model's
    # split thresholds (median ~0.012, consistent with ln(5)
    # divided by delta_radius^2 where delta_radius is in percent,
    # e.g. delta~11.8 -> 1.609/139 ~ 0.0116).
    # -----------------------------------------------------
    def dimensionless_entropy(self, compositions):
        c = np.array(compositions) / 100
        c = c[c > 0]
        return -np.sum(c * np.log(c))

    def omega(self, elements, compositions, delta_h_kjmol):
        entropy = self.mixing_entropy_with_R(compositions)
        tm = self.mean_property(elements, compositions, "melting_point_K")
        dh_jmol = abs(delta_h_kjmol) * 1000.0
        if dh_jmol < 1e-6:
            return 999.0
        return (tm * entropy) / dh_jmol

    def lambda_parameter(self, delta_radius_percent, dimensionless_entropy):
        if delta_radius_percent == 0:
            return 999.0
        return dimensionless_entropy / (delta_radius_percent ** 2)

    # -----------------------------------------------------
    # Main entry point
    # -----------------------------------------------------
    def calculate(self, elements, compositions):

        # IMPORTANT: the training data (atlas_phea.csv) always has
        # el1 < el2 < ... < el5 alphabetically -- verified on the
        # full 1,086,008-row file (100% of rows sorted), and the
        # trained model's split values confirm el1_idx is always
        # the smallest and el5_idx the largest. So elements MUST be
        # sorted the same way before building el*_idx (and before
        # any composition-weighted calculation, compositions must
        # be reordered to match).
        order = sorted(
            range(len(elements)),
            key=lambda i: self.element_index[elements[i]]
        )
        elements = [elements[i] for i in order]
        compositions = [compositions[i] for i in order]

        features = {}

        features["mean_atomic_radius_pm"] = self.mean_property(
            elements, compositions, "atomic_radius_pm"
        )
        features["mean_density"] = self.mean_property(
            elements, compositions, "density"
        )
        features["mean_melting_point_K"] = self.mean_property(
            elements, compositions, "melting_point_K"
        )
        features["mean_electronegativity"] = self.mean_property(
            elements, compositions, "electronegativity"
        )
        features["mean_atomic_mass"] = self.mean_property(
            elements, compositions, "atomic_mass"
        )
        features["mean_vec"] = self.mean_property(
            elements, compositions, "VEC"
        )

        features["std_atomic_radius_pm"] = self.std_property(
            elements, compositions, "atomic_radius_pm"
        )
        features["std_density"] = self.std_property(
            elements, compositions, "density"
        )
        features["std_melting_point_K"] = self.std_property(
            elements, compositions, "melting_point_K"
        )
        features["std_electronegativity"] = self.std_property(
            elements, compositions, "electronegativity"
        )
        features["std_atomic_mass"] = self.std_property(
            elements, compositions, "atomic_mass"
        )

        features["Alloy_DeltaHmix_kJmol"] = self.delta_hmix(
            elements, compositions
        )
        features["delta_radius"] = self.delta_radius(
            elements, compositions
        )

        features["Omega"] = self.omega(
            elements, compositions, features["Alloy_DeltaHmix_kJmol"]
        )
        features["Lambda"] = self.lambda_parameter(
            features["delta_radius"],
            self.dimensionless_entropy(compositions),
        )

        features["el1_idx"] = self.element_index[elements[0]]
        features["el2_idx"] = self.element_index[elements[1]]
        features["el3_idx"] = self.element_index[elements[2]]
        features["el4_idx"] = self.element_index[elements[3]]
        features["el5_idx"] = self.element_index[elements[4]]

        # Return in the EXACT order/set the trained model expects.
        return {name: features[name] for name in self.FEATURE_ORDER}