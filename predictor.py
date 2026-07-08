import joblib
import pandas as pd

from feature_calculator import FeatureCalculator


class Predictor:

    def __init__(self):

        print("Loading AI Model...")

        self.model = joblib.load(
            "models/PHEA_Final_Model.pkl"
        )

        self.calculator = FeatureCalculator()

        print("AI Model Loaded Successfully")

    # ----------------------------------------------------
    # Prediction
    # ----------------------------------------------------

    def predict(self, elements, compositions):

        # Physics Features
        physics = self.calculator.calculate(

            elements,

            compositions

        )

        # Model Input
        X = pd.DataFrame([physics])

        # AI Prediction
        probability = float(

            self.model.predict(X)[0]

        )

        probability = max(

            0,

            min(probability, 1)

        )

        probability_percent = round(

            probability * 100,

            2

        )

        # ---------------------------------------
        # Confidence
        # ---------------------------------------

        if probability_percent >= 95:

            confidence = "Excellent"

        elif probability_percent >= 90:

            confidence = "Very High"

        elif probability_percent >= 80:

            confidence = "High"

        elif probability_percent >= 65:

            confidence = "Moderate"

        else:

            confidence = "Low"

        # ---------------------------------------
        # Interpretation
        # ---------------------------------------

        if probability_percent >= 90:

            interpretation = (
                "Excellent candidate for forming a "
                "Single Phase High Entropy Alloy."
            )

        elif probability_percent >= 75:

            interpretation = (
                "Likely to form a Single Phase High Entropy Alloy."
            )

        elif probability_percent >= 50:

            interpretation = (
                "Borderline alloy. Experimental verification is recommended."
            )

        else:

            interpretation = (
                "Low probability of Single Phase formation."
            )

        # ---------------------------------------
        # Return Result
        # ---------------------------------------

        return {

            "success": True,

            "probability": probability_percent,

            "confidence": confidence,

            "interpretation": interpretation,

            # PDF / Result page
            "elements": elements,

            "compositions": compositions,

            "physics": {

                "DeltaHmix": round(

                    physics["Alloy_DeltaHmix_kJmol"],

                    3

                ),

                "DeltaRadius": round(

                    physics["delta_radius"],

                    3

                ),

                "Omega": round(

                    physics["Omega"],

                    3

                ),

                "Lambda": round(

                    physics["Lambda"],

                    3

                ),

                "VEC": round(

                    physics["mean_vec"],

                    3

                ),

                "MixingEntropy": round(

                    physics.get(

                        "mixing_entropy",

                        1.609

                    ),

                    3

                ),

                "MeanAtomicRadius": round(

                    physics["mean_atomic_radius_pm"],

                    3

                ),

                "MeanDensity": round(

                    physics["mean_density"],

                    3

                ),

                "MeanMeltingPoint": round(

                    physics["mean_melting_point_K"],

                    3

                )

            }

        }
