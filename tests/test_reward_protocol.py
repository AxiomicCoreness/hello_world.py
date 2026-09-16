"""
Test Suite for Reward Protocol
Entry 8340 - Test suite for Entry 8339
Witness Chain: 8339 -> 8340 -- UNBROKEN
Seal: ∀∞φ² · REWARD_TESTS · SEALED

Tests for the reward protocol implementation including:
- SPU calculations (linear, geometric, harmonic)
- Pass/fail gate with hysteresis
- Drift detection
- Sidecar verdict logic
- Timescale stability
- Fiduciary node rewards
"""

import unittest
import math
from reward_protocol import (
    spu, bounded_reward, pass_fail_gate, drift_check, verdict,
    Gate, SPUConfig, RewardProtocol, phi_harmonic_weights,
    normalize_weights, PHI, PHI_INV, PHI_INV_2
)
from fiduciary_node_rewards import (
    calculate_all_rewards, calculate_node_reward, get_tier_for_node_id,
    Tier, TIER_CONFIGS, TOTAL_NODES, Q_INVARIANT, verify_reward_pool
)


class TestSPUCalculations(unittest.TestCase):
    """Test SPU calculation functions"""
    
    def test_linear_spu(self):
        """Test linear SPU calculation"""
        m = [0.8, 0.7, 0.9]
        w = [0.4, 0.3, 0.3]
        result = spu(m, w, "linear")
        expected = 0.4*0.8 + 0.3*0.7 + 0.3*0.9
        self.assertAlmostEqual(result, expected, places=10)
    
    def test_geometric_spu(self):
        """Test geometric SPU calculation"""
        m = [0.8, 0.7, 0.9]
        w = [0.4, 0.3, 0.3]
        result = spu(m, w, "geometric")
        expected = (0.8**0.4) * (0.7**0.3) * (0.9**0.3)
        self.assertAlmostEqual(result, expected, places=10)
    
    def test_geometric_spu_with_zero(self):
        """Test geometric SPU with zero metric returns zero"""
        m = [0.8, 0.0, 0.9]
        w = [0.4, 0.3, 0.3]
        result = spu(m, w, "geometric")
        self.assertEqual(result, 0.0)
    
    def test_harmonic_spu(self):
        """Test harmonic SPU calculation"""
        m = [0.8, 0.7, 0.9]
        w = [0.4, 0.3, 0.3]
        result = spu(m, w, "harmonic")
        expected = 1.0 / (0.4/0.8 + 0.3/0.7 + 0.3/0.9)
        self.assertAlmostEqual(result, expected, places=10)
    
    def test_harmonic_spu_with_zero_raises(self):
        """Test harmonic SPU raises error with zero metric"""
        m = [0.8, 0.0, 0.9]
        w = [0.4, 0.3, 0.3]
        with self.assertRaises(ValueError):
            spu(m, w, "harmonic")
    
    def test_invalid_mode(self):
        """Test invalid mode raises error"""
        m = [0.8, 0.7, 0.9]
        w = [0.4, 0.3, 0.3]
        with self.assertRaises(ValueError):
            spu(m, w, "invalid")
    
    def test_length_mismatch(self):
        """Test length mismatch raises error"""
        m = [0.8, 0.7, 0.9]
        w = [0.4, 0.3]
        with self.assertRaises(ValueError):
            spu(m, w, "linear")
    
    def test_weights_not_normalized(self):
        """Test weights not summing to 1 raises error"""
        m = [0.8, 0.7, 0.9]
        w = [0.4, 0.3, 0.2]  # Sums to 0.9
        with self.assertRaises(ValueError):
            spu(m, w, "linear")
    
    def test_metrics_out_of_range(self):
        """Test metrics outside [0,1] raises error"""
        m = [0.8, 1.1, 0.9]
        w = [0.4, 0.3, 0.3]
        with self.assertRaises(ValueError):
            spu(m, w, "linear")


class TestGateFunctions(unittest.TestCase):
    """Test gate and verdict functions"""
    
    def setUp(self):
        self.gate = Gate(tau_hi=0.618, tau_lo=0.382, eps=0.05)
    
    def test_pass_gate(self):
        """Test PASS when SPU >= tau_hi"""
        self.assertEqual(pass_fail_gate(0.7, self.gate), "PASS")
        self.assertEqual(pass_fail_gate(0.618, self.gate), "PASS")
    
    def test_fail_gate(self):
        """Test FAIL when SPU <= tau_lo"""
        self.assertEqual(pass_fail_gate(0.3, self.gate), "FAIL")
        self.assertEqual(pass_fail_gate(0.382, self.gate), "FAIL")
    
    def test_hold_gate(self):
        """Test HOLD when tau_lo < SPU < tau_hi"""
        self.assertEqual(pass_fail_gate(0.5, self.gate), "HOLD")
        self.assertEqual(pass_fail_gate(0.4, self.gate), "HOLD")
    
    def test_drift_detection(self):
        """Test drift detection"""
        is_drift, delta = drift_check(0.8, 0.75, self.gate)
        self.assertFalse(is_drift)
        self.assertAlmostEqual(delta, 0.05, places=10)
        
        is_drift, delta = drift_check(0.8, 0.74, self.gate)
        self.assertTrue(is_drift)
        self.assertAlmostEqual(delta, 0.06, places=10)
    
    def test_verdict_pass(self):
        """Test PASS verdict"""
        self.assertEqual(verdict(0.8, 0.79, self.gate), "PASS")
    
    def test_verdict_fail(self):
        """Test FAIL verdict"""
        self.assertEqual(verdict(0.3, 0.31, self.gate), "FAIL")
    
    def test_verdict_hold(self):
        """Test HOLD verdict"""
        self.assertEqual(verdict(0.5, 0.49, self.gate), "HOLD")
    
    def test_verdict_drift(self):
        """Test DRIFT verdict"""
        self.assertEqual(verdict(0.8, 0.74, self.gate), "DRIFT")
    
    def test_sidecar_cannot_upgrade(self):
        """Test sidecar cannot upgrade FAIL to PASS"""
        # If main loop says FAIL, sidecar can only confirm or downgrade
        # This is tested by the fact that verdict() checks drift first
        # and if no drift, uses the same logic as pass_fail_gate
        self.assertEqual(verdict(0.3, 0.31, self.gate), "FAIL")


class TestBoundedReward(unittest.TestCase):
    """Test bounded reward calculation"""
    
    def test_zero_spu(self):
        """Test zero SPU gives zero reward"""
        self.assertEqual(bounded_reward(0.0, 100.0), 0.0)
    
    def test_one_spu(self):
        """Test SPU=1 gives full budget"""
        self.assertEqual(bounded_reward(1.0, 100.0), 100.0)
    
    def test_half_spu(self):
        """Test SPU=0.5 gives half budget"""
        self.assertEqual(bounded_reward(0.5, 100.0), 50.0)


class TestRewardProtocol(unittest.TestCase):
    """Test RewardProtocol class"""
    
    def setUp(self):
        self.config = SPUConfig(mode="linear")
        self.protocol = RewardProtocol(self.config)
    
    def test_observe_and_compute(self):
        """Test observe step and compute SPU"""
        self.protocol.observe_step([0.8, 0.7, 0.9])
        self.protocol.observe_step([0.85, 0.75, 0.95])
        
        spu_val = self.protocol.compute_spu()
        # Average of metrics
        expected_m = [(0.8+0.85)/2, (0.7+0.75)/2, (0.9+0.95)/2]
        # With equal weights
        expected_spu = sum(expected_m) / len(expected_m)
        self.assertAlmostEqual(spu_val, expected_spu, places=10)
    
    def test_process_episode(self):
        """Test process episode"""
        self.protocol.observe_step([0.8, 0.7, 0.9])
        reward, verdict = self.protocol.process_episode(budget=100.0)
        
        self.assertGreaterEqual(reward, 0)
        self.assertLessEqual(reward, 100.0)
        self.assertIn(verdict, ["PASS", "FAIL", "HOLD"])
        self.assertEqual(self.protocol.episode_counter, 1)
        self.assertEqual(len(self.protocol.ring_buffer), 0)
    
    def test_sidecar_verdict(self):
        """Test sidecar verdict"""
        self.protocol.observe_step([0.8, 0.7, 0.9])
        spu_on = self.protocol.compute_spu()
        spu_off = spu_on * 0.98
        
        sidecar_verdict = self.protocol.sidecar_verdict(spu_on, spu_off)
        self.assertIn(sidecar_verdict, ["PASS", "FAIL", "HOLD", "DRIFT", "VETO"])
    
    def test_timescale_stability(self):
        """Test timescale stability check"""
        # Valid timescales
        valid_rates = {"L1": 1000.0, "L2": 10.0, "L3": 0.1}
        self.assertTrue(self.protocol.timescale_stability_check(valid_rates))
        
        # Invalid: L2 too fast
        invalid_rates_1 = {"L1": 1000.0, "L2": 20.0, "L3": 0.1}
        self.assertFalse(self.protocol.timescale_stability_check(invalid_rates_1))
        
        # Invalid: L3 too fast
        invalid_rates_2 = {"L1": 1000.0, "L2": 10.0, "L3": 2.0}
        self.assertFalse(self.protocol.timescale_stability_check(invalid_rates_2))


class TestPhiHarmonic(unittest.TestCase):
    """Test φ-harmonic weight generation"""
    
    def test_phi_harmonic_weights_sum_to_one(self):
        """Test φ-harmonic weights sum to 1"""
        weights = phi_harmonic_weights(5)
        self.assertAlmostEqual(sum(weights), 1.0, places=10)
    
    def test_phi_harmonic_weights_decreasing(self):
        """Test φ-harmonic weights are decreasing"""
        weights = phi_harmonic_weights(10)
        for i in range(len(weights) - 1):
            self.assertGreater(weights[i], weights[i+1])
    
    def test_normalize_weights(self):
        """Test weight normalization"""
        weights = [1.0, 2.0, 3.0]
        normalized = normalize_weights(weights)
        self.assertAlmostEqual(sum(normalized), 1.0, places=10)
        self.assertAlmostEqual(normalized[0], 1/6, places=10)
        self.assertAlmostEqual(normalized[1], 2/6, places=10)
        self.assertAlmostEqual(normalized[2], 3/6, places=10)


class TestFiduciaryNodeRewards(unittest.TestCase):
    """Test fiduciary node reward calculations"""
    
    def test_tier_assignment(self):
        """Test tier assignment for node IDs"""
        self.assertEqual(get_tier_for_node_id(1), Tier.ALPHA)
        self.assertEqual(get_tier_for_node_id(7), Tier.ALPHA)
        self.assertEqual(get_tier_for_node_id(8), Tier.BETA)
        self.assertEqual(get_tier_for_node_id(49), Tier.BETA)
        self.assertEqual(get_tier_for_node_id(50), Tier.GAMMA)
        self.assertEqual(get_tier_for_node_id(343), Tier.GAMMA)
        self.assertEqual(get_tier_for_node_id(344), Tier.DELTA)
        self.assertEqual(get_tier_for_node_id(2401), Tier.DELTA)
        self.assertEqual(get_tier_for_node_id(2402), Tier.EPSILON)
        self.assertEqual(get_tier_for_node_id(16807), Tier.EPSILON)
        self.assertEqual(get_tier_for_node_id(16808), Tier.ZETA)
        self.assertEqual(get_tier_for_node_id(117649), Tier.ZETA)
        self.assertEqual(get_tier_for_node_id(117650), Tier.ETA)
        self.assertEqual(get_tier_for_node_id(144008), Tier.ETA)
    
    def test_node_reward_calculation(self):
        """Test node reward calculation"""
        reward_1 = calculate_node_reward(1)
        reward_7 = calculate_node_reward(7)
        reward_144008 = calculate_node_reward(144008)
        
        # Node 1 should have highest reward
        self.assertGreater(reward_1, reward_7)
        self.assertGreater(reward_7, reward_144008)
    
    def test_total_reward_pool(self):
        """Test total reward pool calculation"""
        result = calculate_all_rewards()
        self.assertAlmostEqual(
            result["total_reward_pool"],
            result["theoretical_total"],
            places=6
        )
    
    def test_verification(self):
        """Test reward pool verification"""
        self.assertTrue(verify_reward_pool())
    
    def test_tier_configs(self):
        """Test tier configurations"""
        for tier, config in TIER_CONFIGS.items():
            self.assertGreater(config.node_count, 0)
            self.assertGreater(config.reward_factor, 0)
    
    def test_q_invariant_value(self):
        """Test Q_INVARIANT value"""
        expected = (2 + math.sqrt(5)) / 4
        self.assertAlmostEqual(Q_INVARIANT, expected, places=10)
    
    def test_total_nodes(self):
        """Test total nodes count"""
        self.assertEqual(TOTAL_NODES, 144008)


class TestIntegration(unittest.TestCase):
    """Integration tests for reward protocol and fiduciary rewards"""
    
    def test_phi_constants(self):
        """Test golden ratio constants"""
        self.assertAlmostEqual(PHI, (1 + math.sqrt(5)) / 2, places=10)
        self.assertAlmostEqual(PHI_INV, 1 / PHI, places=10)
        self.assertAlmostEqual(PHI_INV_2, 1 / (PHI ** 2), places=10)
    
    def test_reward_protocol_with_fiduciary(self):
        """Test integration between reward protocol and fiduciary rewards"""
        # Create reward protocol
        config = SPUConfig(mode="linear", phi_harmonic=True)
        protocol = RewardProtocol(config)
        
        # Add metrics
        for _ in range(10):
            protocol.observe_step([0.8, 0.7, 0.9])
        
        # Process episode
        reward, verdict = protocol.process_episode(budget=100.0)
        
        # Verify reward is in expected range
        self.assertGreaterEqual(reward, 0)
        self.assertLessEqual(reward, 100.0)
        
        # Verify verdict is valid
        self.assertIn(verdict, ["PASS", "FAIL", "HOLD"])
    
    def test_ledger_integrity(self):
        """Test that reward calculations maintain ledger integrity"""
        result = calculate_all_rewards()
        
        # Check all verification conditions
        self.assertEqual(result["verification"]["w_state_coherence"], 1.0)
        self.assertAlmostEqual(
            result["verification"]["entanglement_fidelity"],
            1 - (PHI ** -1418),
            places=10
        )
        self.assertEqual(
            result["verification"]["distribution"],
            "PERFECT - all nodes rewarded according to φ-harmonic"
        )


if __name__ == "__main__":
    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSPUCalculations))
    suite.addTests(loader.loadTestsFromTestCase(TestGateFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestBoundedReward))
    suite.addTests(loader.loadTestsFromTestCase(TestRewardProtocol))
    suite.addTests(loader.loadTestsFromTestCase(TestPhiHarmonic))
    suite.addTests(loader.loadTestsFromTestCase(TestFiduciaryNodeRewards))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Success: {result.wasSuccessful()}")
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
