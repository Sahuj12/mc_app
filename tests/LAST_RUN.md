test_correct_credentials_logs_in (tests.test_auth.TestLogin.test_correct_credentials_logs_in) ... INFO:app:New account created: user_id=1
ok
test_dashboard_requires_login (tests.test_auth.TestLogin.test_dashboard_requires_login) ... ok
test_nonexistent_email_rejected (tests.test_auth.TestLogin.test_nonexistent_email_rejected) ... ok
test_wrong_password_rejected (tests.test_auth.TestLogin.test_wrong_password_rejected) ... INFO:app:New account created: user_id=2
ok
test_logout_clears_session_and_blocks_protected_pages (tests.test_auth.TestLogout.test_logout_clears_session_and_blocks_protected_pages) ... INFO:app:New account created: user_id=3
ok
test_invalid_token_rejected (tests.test_auth.TestPasswordReset.test_invalid_token_rejected) ... ok
test_no_email_enumeration (tests.test_auth.TestPasswordReset.test_no_email_enumeration)
Submitting forgot-password for a nonexistent email should look identical to a real one. ... ok
test_reset_flow_end_to_end (tests.test_auth.TestPasswordReset.test_reset_flow_end_to_end) ... INFO:app:New account created: user_id=4
ok
test_duplicate_email_rejected (tests.test_auth.TestRegistration.test_duplicate_email_rejected) ... INFO:app:New account created: user_id=5
ok
test_invalid_email_format_rejected (tests.test_auth.TestRegistration.test_invalid_email_format_rejected) ... ok
test_mismatched_confirmation_rejected (tests.test_auth.TestRegistration.test_mismatched_confirmation_rejected) ... ok
test_password_stored_hashed_not_plaintext (tests.test_auth.TestRegistration.test_password_stored_hashed_not_plaintext) ... INFO:app:New account created: user_id=6
ok
test_valid_registration_succeeds (tests.test_auth.TestRegistration.test_valid_registration_succeeds) ... INFO:app:New account created: user_id=7
ok
test_weak_password_rejected (tests.test_auth.TestRegistration.test_weak_password_rejected) ... ok
test_delete_dataset (tests.test_datasets.TestDatasetUpload.test_delete_dataset) ... INFO:app:New account created: user_id=8
ok
test_upload_empty_file_rejected (tests.test_datasets.TestDatasetUpload.test_upload_empty_file_rejected) ... INFO:app:New account created: user_id=9
ok
test_upload_non_csv_content_rejected_gracefully (tests.test_datasets.TestDatasetUpload.test_upload_non_csv_content_rejected_gracefully) ... INFO:app:New account created: user_id=10
ok
test_upload_valid_price_csv_succeeds (tests.test_datasets.TestDatasetUpload.test_upload_valid_price_csv_succeeds) ... INFO:app:New account created: user_id=11
ok
test_uploaded_dataset_usable_in_bootstrap_simulation (tests.test_datasets.TestDatasetUpload.test_uploaded_dataset_usable_in_bootstrap_simulation) ... INFO:app:New account created: user_id=12
ok
test_png_export_buttons_present_and_reference_correct_canvases (tests.test_export.TestChartExportUI.test_png_export_buttons_present_and_reference_correct_canvases) ... INFO:app:New account created: user_id=13
ok
test_results_js_defines_download_chart_function (tests.test_export.TestChartExportUI.test_results_js_defines_download_chart_function) ... INFO:app:New account created: user_id=14
ok
test_export_csv_expired_token_fails_cleanly (tests.test_export.TestExportCSV.test_export_csv_expired_token_fails_cleanly) ... INFO:app:New account created: user_id=15
ok
test_export_csv_from_saved_run (tests.test_export.TestExportCSV.test_export_csv_from_saved_run) ... INFO:app:New account created: user_id=16
ok
test_export_csv_from_unsaved_run (tests.test_export.TestExportCSV.test_export_csv_from_unsaved_run) ... INFO:app:New account created: user_id=17
ok
test_export_csv_missing_identifier_fails_cleanly (tests.test_export.TestExportCSV.test_export_csv_missing_identifier_fails_cleanly) ... INFO:app:New account created: user_id=18
ok
test_export_json_for_other_users_sim_is_blocked (tests.test_export.TestExportJSON.test_export_json_for_other_users_sim_is_blocked) ... INFO:app:New account created: user_id=19
ok
test_export_json_from_saved_run (tests.test_export.TestExportJSON.test_export_json_from_saved_run) ... INFO:app:New account created: user_id=21
ok
test_export_json_from_unsaved_run (tests.test_export.TestExportJSON.test_export_json_from_unsaved_run) ... INFO:app:New account created: user_id=22
ok
test_new_simulation_form_exposes_optional_fields (tests.test_input_validation.TestOptionalParams.test_new_simulation_form_exposes_optional_fields) ... INFO:app:New account created: user_id=23
ok
test_random_seed_is_optional_and_reproducible (tests.test_input_validation.TestOptionalParams.test_random_seed_is_optional_and_reproducible) ... INFO:app:New account created: user_id=24
ok
test_seed_left_blank_still_runs (tests.test_input_validation.TestOptionalParams.test_seed_left_blank_still_runs) ... INFO:app:New account created: user_id=25
ok
test_all_required_fields_accepted_when_valid (tests.test_input_validation.TestRequiredParams.test_all_required_fields_accepted_when_valid) ... INFO:app:New account created: user_id=26
ok
test_new_simulation_form_exposes_all_required_fields (tests.test_input_validation.TestRequiredParams.test_new_simulation_form_exposes_all_required_fields) ... INFO:app:New account created: user_id=27
ok
test_above_maximum_rejected (tests.test_input_validation.TestSimulationCountLimit.test_above_maximum_rejected) ... INFO:app:New account created: user_id=28
ok
test_at_maximum_allowed_succeeds (tests.test_input_validation.TestSimulationCountLimit.test_at_maximum_allowed_succeeds) ... INFO:app:New account created: user_id=29
ok
test_below_minimum_rejected (tests.test_input_validation.TestSimulationCountLimit.test_below_minimum_rejected) ... INFO:app:New account created: user_id=30
ok
test_form_advertises_the_maximum (tests.test_input_validation.TestSimulationCountLimit.test_form_advertises_the_maximum) ... INFO:app:New account created: user_id=31
ok
test_bootstrap_without_dataset_rejected (tests.test_input_validation.TestValidationErrors.test_bootstrap_without_dataset_rejected) ... INFO:app:New account created: user_id=32
ok
test_cross_field_memory_guardrail (tests.test_input_validation.TestValidationErrors.test_cross_field_memory_guardrail)
A combination that is individually in-range per-field but whose ... INFO:app:New account created: user_id=33
ok
test_invalid_distribution_name_rejected (tests.test_input_validation.TestValidationErrors.test_invalid_distribution_name_rejected) ... INFO:app:New account created: user_id=34
ok
test_negative_initial_price_rejected (tests.test_input_validation.TestValidationErrors.test_negative_initial_price_rejected) ... INFO:app:New account created: user_id=35
ok
test_non_numeric_input_rejected (tests.test_input_validation.TestValidationErrors.test_non_numeric_input_rejected) ... INFO:app:New account created: user_id=36
ok
test_out_of_range_drift_rejected (tests.test_input_validation.TestValidationErrors.test_out_of_range_drift_rejected) ... INFO:app:New account created: user_id=37
ok
test_out_of_range_time_horizon_rejected (tests.test_input_validation.TestValidationErrors.test_out_of_range_time_horizon_rejected) ... INFO:app:New account created: user_id=38
ok
test_out_of_range_volatility_rejected (tests.test_input_validation.TestValidationErrors.test_out_of_range_volatility_rejected) ... INFO:app:New account created: user_id=39
ok
test_valid_input_after_fixing_errors_succeeds (tests.test_input_validation.TestValidationErrors.test_valid_input_after_fixing_errors_succeeds)
Simulates a user correcting a validation error and resubmitting. ... INFO:app:New account created: user_id=40
ok
test_chart_paths_are_subsampled_not_all_simulations (tests.test_output_and_charts.TestChartPayload.test_chart_paths_are_subsampled_not_all_simulations)
Plotting all 5000 paths would be unreadable; the app should subsample. ... INFO:app:New account created: user_id=41
ok
test_chart_payload_has_sample_paths_and_histogram (tests.test_output_and_charts.TestChartPayload.test_chart_payload_has_sample_paths_and_histogram) ... INFO:app:New account created: user_id=42
ok
test_outlier_flags_present_and_bounded (tests.test_output_and_charts.TestChartPayload.test_outlier_flags_present_and_bounded) ... INFO:app:New account created: user_id=43
ok
test_results_page_contains_chart_canvases (tests.test_output_and_charts.TestChartPayload.test_results_page_contains_chart_canvases) ... INFO:app:New account created: user_id=44
ok
test_percentiles_are_monotonically_increasing (tests.test_output_and_charts.TestStatisticalSummary.test_percentiles_are_monotonically_increasing) ... INFO:app:New account created: user_id=45
ok
test_probability_of_loss_is_a_valid_percentage (tests.test_output_and_charts.TestStatisticalSummary.test_probability_of_loss_is_a_valid_percentage) ... INFO:app:New account created: user_id=46
ok
test_summary_language_stays_descriptive_not_advisory (tests.test_output_and_charts.TestStatisticalSummary.test_summary_language_stays_descriptive_not_advisory)
C2: the tool must not give financial advice -- check for the disclaimer language. ... INFO:app:New account created: user_id=47
ok
test_summary_page_contains_key_statistics (tests.test_output_and_charts.TestStatisticalSummary.test_summary_page_contains_key_statistics) ... INFO:app:New account created: user_id=48
ok
test_completely_empty_submission_does_not_crash (tests.test_reliability.TestGracefulFailure.test_completely_empty_submission_does_not_crash) ... INFO:app:New account created: user_id=49
ok
test_malformed_dataset_id_in_bootstrap_run_handled (tests.test_reliability.TestGracefulFailure.test_malformed_dataset_id_in_bootstrap_run_handled) ... INFO:app:New account created: user_id=50
ok
test_missing_required_field_does_not_crash (tests.test_reliability.TestGracefulFailure.test_missing_required_field_does_not_crash) ... INFO:app:New account created: user_id=51
ok
test_nonexistent_page_returns_custom_404 (tests.test_reliability.TestGracefulFailure.test_nonexistent_page_returns_custom_404) ... INFO:app:New account created: user_id=52
ok
test_nonexistent_saved_simulation_returns_404_not_500 (tests.test_reliability.TestGracefulFailure.test_nonexistent_saved_simulation_returns_404_not_500) ... INFO:app:New account created: user_id=53
ok
test_oversized_upload_rejected_cleanly (tests.test_reliability.TestGracefulFailure.test_oversized_upload_rejected_cleanly) ... INFO:app:New account created: user_id=54
ok
test_sql_injection_style_input_does_not_crash_or_succeed (tests.test_reliability.TestGracefulFailure.test_sql_injection_style_input_does_not_crash_or_succeed)
Basic defense-in-depth check: malicious-looking input should be ... INFO:app:New account created: user_id=55
ok
test_delete_removes_from_saved_list (tests.test_save_reopen_delete.TestDeleteSimulation.test_delete_removes_from_saved_list) ... INFO:app:New account created: user_id=56
ok
test_deleted_simulation_no_longer_reachable (tests.test_save_reopen_delete.TestDeleteSimulation.test_deleted_simulation_no_longer_reachable) ... INFO:app:New account created: user_id=57
ok
test_reopen_another_users_simulation_is_blocked (tests.test_save_reopen_delete.TestReopenSimulation.test_reopen_another_users_simulation_is_blocked) ... INFO:app:New account created: user_id=58
ok
test_reopen_shows_original_inputs_and_summary (tests.test_save_reopen_delete.TestReopenSimulation.test_reopen_shows_original_inputs_and_summary) ... INFO:app:New account created: user_id=60
ok
test_expired_or_invalid_token_cannot_be_saved (tests.test_save_reopen_delete.TestSaveSimulation.test_expired_or_invalid_token_cannot_be_saved) ... INFO:app:New account created: user_id=61
ok
test_save_persists_and_redirects_to_saved_view (tests.test_save_reopen_delete.TestSaveSimulation.test_save_persists_and_redirects_to_saved_view) ... INFO:app:New account created: user_id=62
  return super().__new__(cls, object)
ok
test_saved_run_contains_full_summary (tests.test_save_reopen_delete.TestSaveSimulation.test_saved_run_contains_full_summary) ... INFO:app:New account created: user_id=63
ok
test_cannot_exceed_max_saved_simulations (tests.test_save_reopen_delete.TestStorageQuotas.test_cannot_exceed_max_saved_simulations) ... INFO:app:New account created: user_id=64
ok
test_encrypted_blob_round_trips_correctly (tests.test_security.TestEncryptionAtRest.test_encrypted_blob_round_trips_correctly) ... INFO:app:New account created: user_id=65
ok
test_saved_simulation_blob_is_not_plaintext_json (tests.test_security.TestEncryptionAtRest.test_saved_simulation_blob_is_not_plaintext_json) ... INFO:app:New account created: user_id=66
ok
test_tampered_ciphertext_fails_to_decrypt (tests.test_security.TestEncryptionAtRest.test_tampered_ciphertext_fails_to_decrypt) ... INFO:app:New account created: user_id=67
ok
test_uploaded_dataset_encrypted_at_rest (tests.test_security.TestEncryptionAtRest.test_uploaded_dataset_encrypted_at_rest) ... INFO:app:New account created: user_id=68
ok
test_correct_password_verifies (tests.test_security.TestPasswordHashing.test_correct_password_verifies) ... ok
test_hash_is_not_plaintext (tests.test_security.TestPasswordHashing.test_hash_is_not_plaintext) ... ok
test_hash_uses_pbkdf2 (tests.test_security.TestPasswordHashing.test_hash_uses_pbkdf2) ... ok
test_same_password_hashed_twice_produces_different_hashes (tests.test_security.TestPasswordHashing.test_same_password_hashed_twice_produces_different_hashes)
Salting means identical passwords should not produce identical hashes. ... ok
test_wrong_password_fails_verification (tests.test_security.TestPasswordHashing.test_wrong_password_fails_verification) ... ok
test_active_session_stays_logged_in (tests.test_security.TestSessionTimeout.test_active_session_stays_logged_in) ... INFO:app:New account created: user_id=69
ok
test_activity_refreshes_session_timeout (tests.test_security.TestSessionTimeout.test_activity_refreshes_session_timeout)
Each authenticated request should push the timeout window forward. ... INFO:app:New account created: user_id=70
ok
test_stale_session_is_logged_out (tests.test_security.TestSessionTimeout.test_stale_session_is_logged_out) ... INFO:app:New account created: user_id=71
ok
test_bootstrap_distribution_runs_with_historical_returns (tests.test_simulation_engine.TestDistributions.test_bootstrap_distribution_runs_with_historical_returns) ... ok
test_normal_distribution_runs (tests.test_simulation_engine.TestDistributions.test_normal_distribution_runs) ... ok
test_student_t_distribution_runs_and_has_fatter_tails_than_normal (tests.test_simulation_engine.TestDistributions.test_student_t_distribution_runs_and_has_fatter_tails_than_normal) ... ok
test_all_paths_start_at_initial_price (tests.test_simulation_engine.TestMonteCarloEngine.test_all_paths_start_at_initial_price) ... ok
test_different_seeds_produce_different_results (tests.test_simulation_engine.TestMonteCarloEngine.test_different_seeds_produce_different_results) ... ok
test_path_shape_matches_requested_simulations_and_steps (tests.test_simulation_engine.TestMonteCarloEngine.test_path_shape_matches_requested_simulations_and_steps) ... ok
test_prices_never_go_negative (tests.test_simulation_engine.TestMonteCarloEngine.test_prices_never_go_negative)
GBM is mathematically guaranteed to stay positive; verify the implementation preserves this. ... ok
test_same_seed_is_reproducible (tests.test_simulation_engine.TestMonteCarloEngine.test_same_seed_is_reproducible) ... ok
test_zero_volatility_is_deterministic (tests.test_simulation_engine.TestMonteCarloEngine.test_zero_volatility_is_deterministic)
With zero volatility, every path should follow the exact same deterministic drift curve. ... ok
test_all_pages_extend_the_same_navigation_structure (tests.test_usability.TestConsistentDesignSystem.test_all_pages_extend_the_same_navigation_structure) ... INFO:app:New account created: user_id=72
ok
test_all_pages_link_the_same_stylesheet (tests.test_usability.TestConsistentDesignSystem.test_all_pages_link_the_same_stylesheet) ... INFO:app:New account created: user_id=73
ok
test_shared_css_custom_properties_used_consistently (tests.test_usability.TestConsistentDesignSystem.test_shared_css_custom_properties_used_consistently) ... INFO:app:New account created: user_id=74
ok
test_css_enforces_minimum_desktop_width (tests.test_usability.TestDesktopViewport.test_css_enforces_minimum_desktop_width) ... ok
test_mobile_warning_banner_present (tests.test_usability.TestDesktopViewport.test_mobile_warning_banner_present) ... ok
test_viewport_meta_tag_forces_desktop_width (tests.test_usability.TestDesktopViewport.test_viewport_meta_tag_forces_desktop_width) ... ok
test_every_simulation_input_has_a_tooltip (tests.test_usability.TestTooltips.test_every_simulation_input_has_a_tooltip) ... INFO:app:New account created: user_id=75
ok
test_every_statistic_on_results_page_has_a_tooltip (tests.test_usability.TestTooltips.test_every_statistic_on_results_page_has_a_tooltip) ... INFO:app:New account created: user_id=76
ok
test_tooltip_bubbles_contain_actual_explanatory_text (tests.test_usability.TestTooltips.test_tooltip_bubbles_contain_actual_explanatory_text) ... INFO:app:New account created: user_id=77
ok

----------------------------------------------------------------------
Ran 99 tests in 52.426s

OK

Run date: 2026-07-15 02:01 UTC
