# Test Case Index

A complete list of all 99 individual automated test cases, grouped by file
and class, each with a one-line description of what it actually checks.

For which *requirement* each group maps to, see `REQUIREMENTS_TRACEABILITY_MATRIX.md`.
For the raw pass/fail console output of the latest run, see `tests/LAST_RUN.md`.

---

## `test_auth.py` -- 15 tests

### `TestRegistration` (6)
| Test | Checks |
|---|---|
| `test_valid_registration_succeeds` | A well-formed registration redirects to login and actually creates the user in the database. |
| `test_duplicate_email_rejected` | Registering the same email twice is rejected with an "already exists" error. |
| `test_weak_password_rejected` | A password under the minimum length is rejected and no account is created. |
| `test_mismatched_confirmation_rejected` | Password and confirm-password fields not matching is rejected. |
| `test_invalid_email_format_rejected` | A malformed email address (no @/domain) is rejected. |
| `test_password_stored_hashed_not_plaintext` | The stored password is a PBKDF2 hash, never the plaintext password. |

### `TestLogin` (4)
| Test | Checks |
|---|---|
| `test_correct_credentials_logs_in` | Correct email + password logs in and redirects to the dashboard. |
| `test_wrong_password_rejected` | Correct email with the wrong password is rejected with a generic error. |
| `test_nonexistent_email_rejected` | Logging in with an email that was never registered is rejected. |
| `test_dashboard_requires_login` | Visiting the dashboard while logged out redirects to the login page. |

### `TestLogout` (1)
| Test | Checks |
|---|---|
| `test_logout_clears_session_and_blocks_protected_pages` | Logging out clears the session so protected pages become inaccessible again. |

### `TestPasswordReset` (4)
| Test | Checks |
|---|---|
| `test_reset_flow_end_to_end` | Full flow: request reset link, set new password, old password stops working, new password works. |
| `test_invalid_token_rejected` | A garbage/non-existent reset token is rejected and redirects to "forgot password." |
| `test_no_email_enumeration` | Requesting a reset for a real vs. a fake email returns identical responses (can't tell which emails are registered). |

---

## `test_input_validation.py` -- 17 tests

### `TestRequiredParams` (2)
| Test | Checks |
|---|---|
| `test_all_required_fields_accepted_when_valid` | Valid values for all 5 required fields run successfully and are reflected on the results page. |
| `test_new_simulation_form_exposes_all_required_fields` | The simulation form actually renders an editable input for each of the 5 required fields. |

### `TestOptionalParams` (3)
| Test | Checks |
|---|---|
| `test_new_simulation_form_exposes_optional_fields` | The form renders inputs for seed, distribution type, and dataset upload. |
| `test_random_seed_is_optional_and_reproducible` | Running the same inputs with the same seed twice produces identical simulated paths. |
| `test_seed_left_blank_still_runs` | Leaving the seed field empty still runs successfully (it's optional). |

### `TestValidationErrors` (9)
| Test | Checks |
|---|---|
| `test_negative_initial_price_rejected` | A negative initial price is rejected with a field-level error. |
| `test_out_of_range_volatility_rejected` | A negative volatility is rejected. |
| `test_out_of_range_drift_rejected` | A drift value outside the allowed range (e.g. 99 = 9900%) is rejected. |
| `test_out_of_range_time_horizon_rejected` | A time horizon beyond the configured maximum years is rejected. |
| `test_non_numeric_input_rejected` | Submitting text instead of a number for a numeric field is rejected with a clear message. |
| `test_invalid_distribution_name_rejected` | An unrecognized distribution name (not normal/student_t/bootstrap) is rejected. |
| `test_bootstrap_without_dataset_rejected` | Choosing "bootstrap" without selecting or uploading a dataset is rejected. |
| `test_cross_field_memory_guardrail` | A simulations x time-horizon combination that would use too much memory is rejected, even though each field is individually in range. |
| `test_valid_input_after_fixing_errors_succeeds` | After a rejected submission, resubmitting with corrected values succeeds (simulates real user correction). |

### `TestSimulationCountLimit` (4)
| Test | Checks |
|---|---|
| `test_at_maximum_allowed_succeeds` | Requesting exactly the maximum allowed number of simulations succeeds. |
| `test_above_maximum_rejected` | Requesting one more than the maximum is rejected. |
| `test_below_minimum_rejected` | Requesting fewer than the minimum allowed simulations is rejected. |
| `test_form_advertises_the_maximum` | The simulation form's HTML actually displays the configured maximum to the user. |

---

## `test_simulation_engine.py` -- 9 tests

### `TestMonteCarloEngine` (6)
| Test | Checks |
|---|---|
| `test_all_paths_start_at_initial_price` | Every single simulated path begins exactly at the entered initial price. |
| `test_path_shape_matches_requested_simulations_and_steps` | The output array has exactly the requested number of paths and time steps. |
| `test_same_seed_is_reproducible` | Two separate runs with an identical seed and inputs produce bit-for-bit identical terminal prices. |
| `test_different_seeds_produce_different_results` | Two runs with different seeds produce different terminal prices (randomness is actually happening). |
| `test_prices_never_go_negative` | Even under extreme drift/volatility inputs, no simulated price ever goes to zero or negative (mathematically guaranteed by GBM). |
| `test_zero_volatility_is_deterministic` | With volatility set to exactly 0, every path is identical (no randomness left when there's no volatility). |

### `TestDistributions` (3)
| Test | Checks |
|---|---|
| `test_normal_distribution_runs` | The Normal distribution option runs successfully and returns the right number of results. |
| `test_student_t_distribution_runs_and_has_fatter_tails_than_normal` | Student-t with low degrees of freedom actually produces measurably fatter tails (higher kurtosis) than Normal, proving the distribution choice really changes the output. |
| `test_bootstrap_distribution_runs_with_historical_returns` | The bootstrap distribution correctly consumes a real array of historical returns and produces results. |

---

## `test_datasets.py` -- 5 tests

| Test | Checks |
|---|---|
| `test_upload_valid_price_csv_succeeds` | Uploading a well-formed CSV of historical prices succeeds and shows up in the dataset list. |
| `test_upload_empty_file_rejected` | Uploading a completely empty file is rejected with a clear error, not silently accepted. |
| `test_upload_non_csv_content_rejected_gracefully` | Uploading garbage/non-CSV binary content fails cleanly (400-level error page), not a server crash. |
| `test_uploaded_dataset_usable_in_bootstrap_simulation` | A dataset uploaded and saved can actually be selected and used to run a bootstrap simulation afterward. |
| `test_delete_dataset` | Deleting an uploaded dataset removes it from the dataset list. |

---

## `test_output_and_charts.py` -- 8 tests

### `TestChartPayload` (4)
| Test | Checks |
|---|---|
| `test_results_page_contains_chart_canvases` | The results page HTML contains both the price-paths and histogram `<canvas>` elements. |
| `test_chart_payload_has_sample_paths_and_histogram` | The embedded chart data actually includes sample paths and histogram bins/counts. |
| `test_chart_paths_are_subsampled_not_all_simulations` | Requesting 5,000 simulations doesn't try to plot all 5,000 lines -- confirms the chart is subsampled for readability. |
| `test_outlier_flags_present_and_bounded` | The outlier-flagging array is present and has exactly one entry per plotted path. |

### `TestStatisticalSummary` (4)
| Test | Checks |
|---|---|
| `test_summary_page_contains_key_statistics` | All 13 expected statistics (mean, median, std dev, VaR, CVaR, skew, kurtosis, percentiles, etc.) are actually shown on the page. |
| `test_percentiles_are_monotonically_increasing` | The P1 through P99 percentile values are in correct non-decreasing order. |
| `test_probability_of_loss_is_a_valid_percentage` | The "probability of loss" statistic is a sane percentage between 0% and 100%. |
| `test_summary_language_stays_descriptive_not_advisory` | The results page never uses advisory phrasing like "you should buy/sell" or "we recommend" -- stays statistical, not advice. |

---

## `test_save_reopen_delete.py` -- 8 tests

### `TestSaveSimulation` (3)
| Test | Checks |
|---|---|
| `test_save_persists_and_redirects_to_saved_view` | Saving a run stores it and redirects to a page showing the original input values. |
| `test_saved_run_contains_full_summary` | A saved simulation retains its full statistical summary, not just the raw inputs. |
| `test_expired_or_invalid_token_cannot_be_saved` | Trying to save using an expired/fake token is rejected with a clear message. |

### `TestReopenSimulation` (2)
| Test | Checks |
|---|---|
| `test_reopen_shows_original_inputs_and_summary` | Reopening a saved simulation shows the exact original inputs and a "reopened from saved" notice. |
| `test_reopen_another_users_simulation_is_blocked` | A different logged-in user cannot open someone else's saved simulation by guessing its ID (returns 404). |

### `TestDeleteSimulation` (2)
| Test | Checks |
|---|---|
| `test_delete_removes_from_saved_list` | Deleting a saved simulation removes it from the saved list. |
| `test_deleted_simulation_no_longer_reachable` | After deletion, directly visiting that simulation's URL returns 404, not stale data. |

### `TestStorageQuotas` (1)
| Test | Checks |
|---|---|
| `test_cannot_exceed_max_saved_simulations` | Trying to save more than the configured per-user limit is blocked once the cap is hit, and the saved list never exceeds it. |

---

## `test_export.py` -- 9 tests

### `TestExportCSV` (4)
| Test | Checks |
|---|---|
| `test_export_csv_from_unsaved_run` | Exporting CSV from a just-run (not yet saved) simulation returns correct headers and the right parameter values. |
| `test_export_csv_from_saved_run` | Exporting CSV from a previously saved simulation works and includes its parameters. |
| `test_export_csv_missing_identifier_fails_cleanly` | Requesting a CSV export with no token or sim_id at all returns a clean 400, not a crash. |
| `test_export_csv_expired_token_fails_cleanly` | Requesting a CSV export with a fake/expired token returns a clean 404. |

### `TestExportJSON` (3)
| Test | Checks |
|---|---|
| `test_export_json_from_unsaved_run` | JSON export from an unsaved run contains parameters, summary statistics, and sample terminal prices with correct values. |
| `test_export_json_from_saved_run` | JSON export also works correctly for a previously saved simulation. |
| `test_export_json_for_other_users_sim_is_blocked` | A different user cannot export someone else's saved simulation by guessing its ID (returns 404). |

### `TestChartExportUI` (2)
| Test | Checks |
|---|---|
| `test_png_export_buttons_present_and_reference_correct_canvases` | The "export as PNG" buttons on the results page are wired to the correct chart canvas IDs. |
| `test_results_js_defines_download_chart_function` | The client-side JS file actually defines the PNG-download function and uses proper image encoding. |

---

## `test_security.py` -- 12 tests

### `TestPasswordHashing` (5)
| Test | Checks |
|---|---|
| `test_hash_is_not_plaintext` | A hashed password is never equal to the original plaintext password. |
| `test_hash_uses_pbkdf2` | The hash format is specifically PBKDF2 (the intended algorithm), not something weaker. |
| `test_correct_password_verifies` | The correct password against its own hash verifies successfully. |
| `test_wrong_password_fails_verification` | An incorrect password against a real hash fails verification. |
| `test_same_password_hashed_twice_produces_different_hashes` | Hashing the identical password twice produces two different hashes (confirms proper salting). |

### `TestEncryptionAtRest` (4)
| Test | Checks |
|---|---|
| `test_saved_simulation_blob_is_not_plaintext_json` | The actual bytes stored in the database for a saved simulation are ciphertext, not readable JSON. |
| `test_encrypted_blob_round_trips_correctly` | Data encrypted and then decrypted comes back byte-for-byte identical to the original. |
| `test_tampered_ciphertext_fails_to_decrypt` | Deliberately corrupting one byte of encrypted data causes decryption to fail loudly, not silently return garbage. |
| `test_uploaded_dataset_encrypted_at_rest` | Uploaded dataset contents are also stored encrypted, not as plaintext. |

### `TestSessionTimeout` (3)
| Test | Checks |
|---|---|
| `test_active_session_stays_logged_in` | A session within the timeout window stays logged in normally. |
| `test_stale_session_is_logged_out` | A session whose last-activity timestamp is older than the configured timeout is force-logged-out. |
| `test_activity_refreshes_session_timeout` | Making a request close to (but before) the timeout resets the clock, extending the session. |

---

## `test_usability.py` -- 9 tests

### `TestTooltips` (3)
| Test | Checks |
|---|---|
| `test_every_simulation_input_has_a_tooltip` | The simulation input form has at least one tooltip icon per documented input field. |
| `test_every_statistic_on_results_page_has_a_tooltip` | The results page has a tooltip for every statistic tile shown. |
| `test_tooltip_bubbles_contain_actual_explanatory_text` | Tooltip bubbles contain real explanatory text, not empty placeholders. |

### `TestDesktopViewport` (3)
| Test | Checks |
|---|---|
| `test_viewport_meta_tag_forces_desktop_width` | The page's viewport meta tag forces a fixed desktop width rather than a mobile-responsive one. |
| `test_mobile_warning_banner_present` | A "designed for desktop browsers" warning banner exists in the page markup. |
| `test_css_enforces_minimum_desktop_width` | The stylesheet defines and enforces a minimum desktop width constraint. |

### `TestConsistentDesignSystem` (3)
| Test | Checks |
|---|---|
| `test_all_pages_link_the_same_stylesheet` | Every major page (login, register, dashboard, simulate, saved, datasets) links the identical shared stylesheet. |
| `test_all_pages_extend_the_same_navigation_structure` | Pages share the same top navigation bar and footer structure. |
| `test_shared_css_custom_properties_used_consistently` | The core design-system CSS variables (colors, radius, fonts) are all defined in the shared stylesheet. |

---

## `test_reliability.py` -- 7 tests

| Test | Checks |
|---|---|
| `test_missing_required_field_does_not_crash` | Omitting a required field entirely returns a clean 400, not a server error. |
| `test_completely_empty_submission_does_not_crash` | Submitting a totally empty form returns a clean 400, not a crash. |
| `test_oversized_upload_rejected_cleanly` | A file upload over the configured size limit is rejected cleanly, not a crash. |
| `test_nonexistent_saved_simulation_returns_404_not_500` | Requesting a saved simulation ID that doesn't exist returns 404, not an unhandled error. |
| `test_nonexistent_page_returns_custom_404` | Visiting a URL that doesn't exist anywhere in the app shows the app's own styled 404 page. |
| `test_malformed_dataset_id_in_bootstrap_run_handled` | Submitting a non-numeric dataset ID during a bootstrap run fails cleanly (this test caught a real bug -- see below). |
| `test_sql_injection_style_input_does_not_crash_or_succeed` | SQL-injection-style text in a numeric field is safely rejected as invalid input, and the database remains intact afterward. |

---

## Summary

**99 tests total**, organized across 9 files covering every functional and
non-functional requirement in the original specification (see
`REQUIREMENTS_TRACEABILITY_MATRIX.md` for the requirement-level mapping).

Two of these tests -- `test_malformed_dataset_id_in_bootstrap_run_handled`
and the equivalent check in `test_export.py` -- caught genuine bugs during
development (unhandled server crashes on malformed IDs), which were fixed
in `sim_routes.py` and `export_routes.py`. Those same tests now serve as
permanent regression guards against that failure mode recurring.
