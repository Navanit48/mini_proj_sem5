import { useLocation, useNavigate } from 'react-router-dom';
import { MessageCircle } from 'lucide-react';

const AssistantLauncher = () => {
  const navigate = useNavigate();
  const location = useLocation();
  if (location.pathname === '/assistant') return null;

  return (
    <button
      type="button"
      onClick={() => navigate('/assistant')}
      aria-label="Open AidFlow assistant"
      title="Ask AidFlow"
      className="fixed bottom-5 right-5 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg shadow-black/30 transition hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background"
    >
      <MessageCircle className="h-6 w-6" />
    </button>
  );
};

export default AssistantLauncher;
