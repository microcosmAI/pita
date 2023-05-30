import numpy as np


class MultivariateUniform:
    """Generates a multivariate uniform distribution.

    Parameters:
        ranges (list[tuple]): Each tuple defines the range (low, high) for one dimension.

    Returns:
        (tuple[np.ndarray, np.ndarray]): An array of shape (num_samples, len(ranges)), where each row is a sample from the multivariate uniform distribution.
    """

    def __call__(self, ranges: list[tuple]) -> tuple[np.ndarray, np.ndarray]:
        # Generate samples for each dimension
        samples = [
            np.random.uniform(low=low, high=high, size=1) for low, high in ranges
        ]

        # Combine the samples for each dimension
        multivariate_samples = np.column_stack(samples)

        return multivariate_samples[0][0], multivariate_samples[0][1]
