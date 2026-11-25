-- Conversation history for the authenticated AidFlow assistant.
CREATE TABLE IF NOT EXISTS public.assistant_conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL DEFAULT 'New conversation',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (id, user_id)
);

CREATE TABLE IF NOT EXISTS public.assistant_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT assistant_messages_conversation_owner_fk
    FOREIGN KEY (conversation_id, user_id)
    REFERENCES public.assistant_conversations(id, user_id)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_assistant_conversations_user_updated
  ON public.assistant_conversations(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_assistant_messages_conversation_created
  ON public.assistant_messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_assistant_messages_user
  ON public.assistant_messages(user_id);

ALTER TABLE public.assistant_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assistant_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS assistant_conversations_owner ON public.assistant_conversations;
CREATE POLICY assistant_conversations_owner
  ON public.assistant_conversations
  FOR ALL TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS assistant_messages_owner ON public.assistant_messages;
CREATE POLICY assistant_messages_owner
  ON public.assistant_messages
  FOR ALL TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (
    auth.uid() = user_id
    AND EXISTS (
      SELECT 1
      FROM public.assistant_conversations c
      WHERE c.id = conversation_id AND c.user_id = auth.uid()
    )
  );

GRANT SELECT, INSERT, UPDATE, DELETE
  ON public.assistant_conversations, public.assistant_messages
  TO authenticated, service_role;
