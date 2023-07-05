import numpy as np


class MultivariateUniform:
    """Multivariate uniform distribution."""

    def __call__(self, ranges: list[tuple]) -> tuple[np.ndarray, np.ndarray]:
        """Generates a multivariate uniform distribution.

        Parameters:
            ranges (list[tuple]): Each tuple defines the range (low, high) for one dimension.

        Returns:
            xy_output = (tuple[np.ndarray, np.ndarray]): An array where each row is a sample
                from the multivariate uniform distribution.
        """
        # Generate samples for each dimension
        samples = [
            np.random.uniform(low=low, high=high, size=1) for low, high in ranges
        ]

        # Combine the samples for each dimension
        multivariate_samples = np.column_stack(samples)

        xy_output = (multivariate_samples[0][0], multivariate_samples[0][1])

        return xy_output