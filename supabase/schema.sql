-- Supabase Schema for ONA Application

-- Enable Row Level Security (RLS)
ALTER DATABASE postgres SET "anon.strict_security" TO "on";

-- PROFILES TABLE
-- Stores user psychological profiles
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    profile_type TEXT,  -- Intellectual, Emotional, Practical, Creative
    profile_data JSONB,  -- Full profile data in JSON format
    personality_traits JSONB  -- Detailed personality traits
);

-- SURVEY RESPONSES TABLE
-- Stores individual survey question responses
CREATE TABLE IF NOT EXISTS survey_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL,
    question_id TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, question_id)
);

-- REMINDERS TABLE
-- Stores user reminders for meditations and other activities
CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL,
    reminder_type TEXT NOT NULL,  -- meditation, practice, etc.
    reminder_time TIME NOT NULL,
    reminder_days TEXT[],  -- Array of days (Monday, Tuesday, etc.)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- USER STATS TABLE
-- Stores usage statistics for each user
CREATE TABLE IF NOT EXISTS user_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT UNIQUE NOT NULL,
    survey_completed BOOLEAN DEFAULT FALSE,
    meditation_count INTEGER DEFAULT 0,
    last_meditation_type TEXT,
    last_meditation_at TIMESTAMP WITH TIME ZONE,
    voice_messages_count INTEGER DEFAULT 0,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- CONVERSATIONS TABLE
-- Stores conversation history
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL,
    message_text TEXT NOT NULL,
    is_user BOOLEAN NOT NULL,  -- TRUE if message from user, FALSE if from bot
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row Level Security Policies
-- Ensure users can only access their own data

-- Profiles RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY profiles_select_policy ON profiles
    FOR SELECT USING (auth.uid()::TEXT = user_id::TEXT);
    
CREATE POLICY profiles_insert_policy ON profiles
    FOR INSERT WITH CHECK (auth.uid()::TEXT = user_id::TEXT);
    
CREATE POLICY profiles_update_policy ON profiles
    FOR UPDATE USING (auth.uid()::TEXT = user_id::TEXT);

-- Survey Responses RLS
ALTER TABLE survey_responses ENABLE ROW LEVEL SECURITY;

CREATE POLICY survey_responses_select_policy ON survey_responses
    FOR SELECT USING (auth.uid()::TEXT = user_id::TEXT);
    
CREATE POLICY survey_responses_insert_policy ON survey_responses
    FOR INSERT WITH CHECK (auth.uid()::TEXT = user_id::TEXT);

-- Reminders RLS
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;

CREATE POLICY reminders_select_policy ON reminders
    FOR SELECT USING (auth.uid()::TEXT = user_id::TEXT);
    
CREATE POLICY reminders_insert_policy ON reminders
    FOR INSERT WITH CHECK (auth.uid()::TEXT = user_id::TEXT);
    
CREATE POLICY reminders_update_policy ON reminders
    FOR UPDATE USING (auth.uid()::TEXT = user_id::TEXT);
    
CREATE POLICY reminders_delete_policy ON reminders
    FOR DELETE USING (auth.uid()::TEXT = user_id::TEXT);

-- User Stats RLS
ALTER TABLE user_stats ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_stats_select_policy ON user_stats
    FOR SELECT USING (auth.uid()::TEXT = user_id::TEXT);
    
CREATE POLICY user_stats_insert_policy ON user_stats
    FOR INSERT WITH CHECK (auth.uid()::TEXT = user_id::TEXT);
    
CREATE POLICY user_stats_update_policy ON user_stats
    FOR UPDATE USING (auth.uid()::TEXT = user_id::TEXT);

-- Conversations RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY conversations_select_policy ON conversations
    FOR SELECT USING (auth.uid()::TEXT = user_id::TEXT);
    
CREATE POLICY conversations_insert_policy ON conversations
    FOR INSERT WITH CHECK (auth.uid()::TEXT = user_id::TEXT);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_survey_responses_user_id ON survey_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_user_stats_user_id ON user_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);

-- Trigger to automatically update the updated_at field
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply the trigger to tables with updated_at
CREATE TRIGGER set_timestamp_profiles
BEFORE UPDATE ON profiles
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_reminders
BEFORE UPDATE ON reminders
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_user_stats
BEFORE UPDATE ON user_stats
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp(); 