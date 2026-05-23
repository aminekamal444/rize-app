-- Replace YOUR_USER_ID
UPDATE profiles 
SET 
  onboarding_step = 3,
  archetype = NULL,
  target_archetype = NULL,
  baseline_score = NULL
WHERE id = '024de95f-91e0-40bc-93cb-fe22f059404f';

DELETE FROM daily_actions WHERE user_id = '024de95f-91e0-40bc-93cb-fe22f059404f';
DELETE FROM daily_plans WHERE user_id = '024de95f-91e0-40bc-93cb-fe22f059404f';

DELETE FROM photos 
WHERE user_id = '024de95f-91e0-40bc-93cb-fe22f059404f'
  AND type IN ('baseline', 'baseline_front', 'baseline_side', 'baseline_body');