"""
Tests for the Monte Carlo simulation engine itself (REQ-OUT-01, REQ-IN-02
distribution options). These test mc_engine.py directly, without going
through HTTP, since this is where the actual analytical correctness lives.
"""
import unittest
import numpy as np

from mc_engine import SimulationParams, run_simulation, compute_summary_statistics


class TestMonteCarloEngine(unittest.TestCase):
    """REQ-OUT-01: Run Monte Carlo simulation."""

    def test_all_paths_start_at_initial_price(self):
        params = SimulationParams(
            initial_price=150, drift=0.05, volatility=0.2,
            time_horizon_years=1, num_simulations=200, random_seed=1,
        )
        result = run_simulation(params)
        self.assertTrue(np.all(result["paths"][:, 0] == 150))

    def test_path_shape_matches_requested_simulations_and_steps(self):
        params = SimulationParams(
            initial_price=100, drift=0.05, volatility=0.2,
            time_horizon_years=1, num_simulations=300, random_seed=1,
        )
        result = run_simulation(params)
        expected_steps = round(1 * params.steps_per_year) + 1  # +1 for the initial price column
        self.assertEqual(result["paths"].shape, (300, expected_steps))

    def test_same_seed_is_reproducible(self):
        p1 = SimulationParams(initial_price=100, drift=0.07, volatility=0.2,
                               time_horizon_years=1, num_simulations=100, random_seed=42)
        p2 = SimulationParams(initial_price=100, drift=0.07, volatility=0.2,
                               time_horizon_years=1, num_simulations=100, random_seed=42)
        r1 = run_simulation(p1)
        r2 = run_simulation(p2)
        np.testing.assert_array_equal(r1["terminal_prices"], r2["terminal_prices"])

    def test_different_seeds_produce_different_results(self):
        p1 = SimulationParams(initial_price=100, drift=0.07, volatility=0.2,
                               time_horizon_years=1, num_simulations=100, random_seed=1)
        p2 = SimulationParams(initial_price=100, drift=0.07, volatility=0.2,
                               time_horizon_years=1, num_simulations=100, random_seed=2)
        r1 = run_simulation(p1)
        r2 = run_simulation(p2)
        self.assertFalse(np.array_equal(r1["terminal_prices"], r2["terminal_prices"]))

    def test_prices_never_go_negative(self):
        """GBM is mathematically guaranteed to stay positive; verify the implementation preserves this."""
        params = SimulationParams(initial_price=100, drift=-0.3, volatility=1.5,
                                   time_horizon_years=2, num_simulations=2000, random_seed=7)
        result = run_simulation(params)
        self.assertTrue(np.all(result["paths"] > 0))

    def test_zero_volatility_is_deterministic(self):
        """With zero volatility, every path should follow the exact same deterministic drift curve."""
        import warnings
        params = SimulationParams(initial_price=100, drift=0.05, volatility=0.0,
                                   time_horizon_years=1, num_simulations=50, random_seed=1)
        with warnings.catch_warnings():
            # scipy's skew/kurtosis warn about precision loss when all values
            # are identical (expected here, since volatility=0 means every
            # path is deterministic) -- this is a known, harmless artifact of
            # this specific edge case, not a bug.
            warnings.simplefilter("ignore", category=RuntimeWarning)
            result = run_simulation(params)
        self.assertTrue(np.allclose(result["paths"], result["paths"][0]))


class TestDistributions(unittest.TestCase):
    """REQ-IN-02: distribution type is a selectable optional parameter."""

    def test_normal_distribution_runs(self):
        params = SimulationParams(initial_price=100, drift=0.05, volatility=0.2,
                                   time_horizon_years=1, num_simulations=200,
                                   distribution="normal", random_seed=1)
        result = run_simulation(params)
        self.assertEqual(result["terminal_prices"].shape, (200,))

    def test_student_t_distribution_runs_and_has_fatter_tails_than_normal(self):
        common = dict(initial_price=100, drift=0.0, volatility=0.2,
                      time_horizon_years=1, num_simulations=5000, random_seed=3)
        normal_params = SimulationParams(distribution="normal", **common)
        t_params = SimulationParams(distribution="student_t", student_t_dof=3, **common)

        normal_result = run_simulation(normal_params)
        t_result = run_simulation(t_params)

        normal_kurt = compute_summary_statistics(normal_result["terminal_prices"], 100)["excess_kurtosis"]
        t_kurt = compute_summary_statistics(t_result["terminal_prices"], 100)["excess_kurtosis"]
        self.assertGreater(t_kurt, normal_kurt, "student-t with low dof should show fatter tails (higher kurtosis)")

    def test_bootstrap_distribution_runs_with_historical_returns(self):
        rng = np.random.default_rng(5)
        synthetic_returns = rng.normal(0.0004, 0.01, size=500)
        params = SimulationParams(
            initial_price=100, drift=0.05, volatility=0.2, time_horizon_years=1,
            num_simulations=200, distribution="bootstrap", random_seed=1,
            bootstrap_returns=synthetic_returns,
        )
        result = run_simulation(params)
        self.assertEqual(result["terminal_prices"].shape, (200,))


if __name__ == "__main__":
    unittest.main()
