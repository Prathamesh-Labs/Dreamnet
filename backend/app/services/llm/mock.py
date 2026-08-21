from app.services.llm.base import BaseLLMProvider
from typing import Any

class MockProvider(BaseLLMProvider):
    def generate_hypotheses(self, question: str) -> list[dict[str, Any]]:
        print(f"[MockProvider] Generating hypotheses for question: '{question}'")
        
        # Check if question is related to ML cost/latency
        q_lower = question.lower()
        if "cost" in q_lower or "latency" in q_lower or "accuracy" in q_lower or "inference" in q_lower:
            return [
                {
                    "statement": "Model quantization (INT8) reduces inference latency and memory footprint by replacing FP32 tensors, with negligible impact on model accuracy.",
                    "rationale": "Integer operations execute faster on hardware supporting INT8 vector instructions (e.g. AVX-512, Tensor Cores), and smaller representations reduce DRAM bandwidth bottlenecks.",
                    "assumptions": [
                        "The target execution hardware has optimized INT8 execution pathways.",
                        "Calibration datasets are representative of production distribution."
                    ],
                    "variables": [
                        "quantization_bits (8-bit vs 32-bit)",
                        "calibration_set_size",
                        "inference_latency",
                        "test_accuracy"
                    ],
                    "predicted_outcome": "INT8 quantization will reduce inference latency by 2x to 3x, while final test accuracy drops by less than 1.5%.",
                    "confidence": 0.85,
                    "testability": "HIGH"
                },
                {
                    "statement": "Knowledge distillation from a complex teacher network (e.g., ResNet-50) to a lightweight student (e.g., MobileNet) provides a better latency/accuracy frontier than quantization alone.",
                    "rationale": "The student model inherits soft probabilities representing inter-class similarity structures from the teacher, allowing a smaller parameter footprint to approximate the teacher's decision boundary.",
                    "assumptions": [
                        "A fully trained teacher model is accessible.",
                        "The dataset is large enough to allow convergence during student distillation."
                    ],
                    "variables": [
                        "student_model_architecture",
                        "temperature_parameter",
                        "inference_latency",
                        "test_accuracy"
                    ],
                    "predicted_outcome": "The distilled student model achieves equivalent accuracy to the teacher while utilizing 1/5th the parameters, outperforming simple post-training quantization in retention of tail-distribution accuracy.",
                    "confidence": 0.75,
                    "testability": "HIGH"
                },
                {
                    "statement": "Input image resolution scaling dynamic pruning matches static latency reduction methods without requiring any training modifications.",
                    "rationale": "Reducing resolution on simple classification samples reduces spatial execution requirements, bypassing FLOPs in early convolutional blocks dynamically.",
                    "assumptions": [
                        "A lightweight router model can evaluate image complexity beforehand.",
                        "Dynamic spatial execution is supported by the inference runtime."
                    ],
                    "variables": [
                        "dynamic_resolution_threshold",
                        "inference_latency",
                        "test_accuracy"
                    ],
                    "predicted_outcome": "Dynamic scaling reduces average latency by 35% with less than 0.5% drop in total accuracy across the test set.",
                    "confidence": 0.65,
                    "testability": "MEDIUM"
                }
            ]
        
        # Generic fallback hypotheses
        return [
            {
                "statement": f"Standard parametric adjustments will establish a significant correlation with the dependent metrics for: {question}.",
                "rationale": "Varying parameter values is the primary mechanical pathway to observe changes in output performance profiles.",
                "assumptions": ["A stable test harness can be constructed.", "Variables can be isolated."],
                "variables": ["parameter_scale", "execution_accuracy"],
                "predicted_outcome": "Higher parameters values will lead to monotonic performance increments up to a plateau.",
                "confidence": 0.70,
                "testability": "HIGH"
            },
            {
                "statement": f"Dynamic learning schedules will outperform static adjustments when solving: {question}.",
                "rationale": "Static structures suffer from convergence bottlenecks. Introducing dynamic adjustments allows exploration-exploitation trade-offs.",
                "assumptions": ["Scheduler configuration parameters can be simulated."],
                "variables": ["scheduler_type", "convergence_epoch"],
                "predicted_outcome": "Dynamic scheduling reduces total training time by 20%.",
                "confidence": 0.60,
                "testability": "MEDIUM"
            },
            {
                "statement": f"Feature engineering modifications will yield higher stability than raw scale enhancements for: {question}.",
                "rationale": "Dimensionality reduction techniques filter noise out of structural inputs, stabilizing model outcomes.",
                "assumptions": ["Noise thresholds are measurable."],
                "variables": ["dimensionality_reduction_ratio", "output_variance"],
                "predicted_outcome": "Variance will decrease by 15% with optimized feature extraction filters.",
                "confidence": 0.55,
                "testability": "MEDIUM"
            }
        ]
