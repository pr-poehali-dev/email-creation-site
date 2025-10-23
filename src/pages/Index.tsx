import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

const API_AUTH = 'https://functions.poehali.dev/3f0551e1-bc02-4729-b5a7-44c4a375efe8';
const API_EMAILS = 'https://functions.poehali.dev/99c710f2-54ee-43c5-b94f-d4a816d686d9';

interface User {
  id: number;
  username: string;
  email: string;
}

interface Email {
  id: number;
  from?: string;
  to?: string;
  subject: string;
  body: string;
  is_read: boolean;
  sent_at: string;
}

export default function Index() {
  const [view, setView] = useState<'auth' | 'dashboard'>('auth');
  const [authMode, setAuthMode] = useState<'login' | 'register'>('register');
  const [user, setUser] = useState<User | null>(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [activeSection, setActiveSection] = useState('inbox');
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCompose, setShowCompose] = useState(false);
  const [composeTo, setComposeTo] = useState('');
  const [composeSubject, setComposeSubject] = useState('');
  const [composeBody, setComposeBody] = useState('');
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (user) {
      loadEmails(activeSection);
    }
  }, [user, activeSection]);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch(API_AUTH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: authMode,
          username,
          password
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setUser(data.user);
        setView('dashboard');
        toast({
          title: authMode === 'register' ? 'Account created!' : 'Welcome back!',
          description: `Logged in as ${data.user.email}`,
        });
      } else {
        toast({
          title: 'Error',
          description: data.error || 'Authentication failed',
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to connect to server',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const loadEmails = async (box: string) => {
    if (!user) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_EMAILS}?box=${box}`, {
        headers: { 'X-User-Id': user.id.toString() }
      });
      
      const data = await response.json();
      if (response.ok) {
        setEmails(data.emails || []);
      }
    } catch (error) {
      console.error('Failed to load emails:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendEmail = async (isDraft = false) => {
    if (!user || !composeTo || !composeSubject || !composeBody) {
      toast({
        title: 'Error',
        description: 'Please fill in all fields',
        variant: 'destructive'
      });
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch(API_EMAILS, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': user.id.toString()
        },
        body: JSON.stringify({
          action: isDraft ? 'draft' : 'send',
          recipient_email: composeTo,
          subject: composeSubject,
          body: composeBody
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        toast({
          title: isDraft ? 'Draft saved' : 'Email sent!',
          description: data.message
        });
        setShowCompose(false);
        setComposeTo('');
        setComposeSubject('');
        setComposeBody('');
        loadEmails(activeSection);
      } else {
        toast({
          title: 'Error',
          description: data.error || 'Failed to send email',
          variant: 'destructive'
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to connect to server',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  if (view === 'auth') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0066CC]/5 via-white to-[#0066CC]/10 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-2xl border-0 animate-fade-in">
          <CardHeader className="space-y-1 text-center pb-8">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-[#0066CC] to-[#0052A3] rounded-2xl flex items-center justify-center mb-4 shadow-lg">
              <Icon name="Mail" size={32} className="text-white" />
            </div>
            <CardTitle className="text-3xl font-bold tracking-tight">SKZRY Mail</CardTitle>
            <CardDescription className="text-base">
              {authMode === 'register' ? 'Create your @skzry.ru email' : 'Sign in to your account'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAuth} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-sm font-medium">Username</Label>
                <Input
                  id="username"
                  placeholder="Enter username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="h-11"
                  required
                />
                <p className="text-xs text-muted-foreground">Your email: {username || 'username'}@skzry.ru</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-medium">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder={authMode === 'register' ? 'Create password' : 'Enter password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-11"
                  required
                />
              </div>
              <Button 
                type="submit" 
                className="w-full h-11 text-base font-medium bg-[#0066CC] hover:bg-[#0052A3]"
                disabled={loading}
              >
                {loading ? 'Processing...' : authMode === 'register' ? 'Create Account' : 'Sign In'}
                <Icon name="ArrowRight" size={18} className="ml-2" />
              </Button>
            </form>
            <div className="mt-4 text-center">
              <button
                onClick={() => setAuthMode(authMode === 'register' ? 'login' : 'register')}
                className="text-sm text-[#0066CC] hover:underline"
              >
                {authMode === 'register' ? 'Already have an account? Sign in' : "Don't have an account? Register"}
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F5F5F5]">
      <header className="bg-gradient-to-r from-[#0066CC] to-[#0052A3] text-white shadow-lg">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur-sm">
              <Icon name="Mail" size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">SKZRY Mail</h1>
              <p className="text-xs text-white/80">{user?.email}</p>
            </div>
          </div>
          <Button 
            variant="ghost" 
            className="text-white hover:bg-white/20"
            onClick={() => {
              setUser(null);
              setView('auth');
              setUsername('');
              setPassword('');
            }}
          >
            <Icon name="LogOut" size={18} className="mr-2" />
            Sign Out
          </Button>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <aside className="lg:col-span-1">
            <Card className="border-0 shadow-md">
              <CardContent className="p-4">
                <Button 
                  className="w-full mb-4 bg-[#0066CC] hover:bg-[#0052A3]"
                  onClick={() => setShowCompose(true)}
                >
                  <Icon name="Plus" size={18} className="mr-2" />
                  Compose
                </Button>
                <div className="space-y-1">
                  {[
                    { id: 'inbox', icon: 'Mail', label: 'Inbox' },
                    { id: 'sent', icon: 'Send', label: 'Sent' },
                    { id: 'drafts', icon: 'FileText', label: 'Drafts' },
                  ].map((item) => (
                    <button
                      key={item.id}
                      onClick={() => setActiveSection(item.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                        activeSection === item.id
                          ? 'bg-[#0066CC] text-white shadow-md'
                          : 'text-[#1A1A1A] hover:bg-[#F5F5F5]'
                      }`}
                    >
                      <Icon name={item.icon as any} size={20} />
                      <span className="flex-1 text-left font-medium text-sm">{item.label}</span>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </aside>

          <main className="lg:col-span-3">
            <Card className="border-0 shadow-md">
              <CardHeader className="border-b bg-white">
                <CardTitle className="text-xl capitalize">{activeSection}</CardTitle>
                <CardDescription>
                  {activeSection === 'inbox' && 'Your received messages'}
                  {activeSection === 'sent' && 'Messages you sent'}
                  {activeSection === 'drafts' && 'Your saved drafts'}
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {loading ? (
                  <div className="p-8 text-center text-muted-foreground">
                    <Icon name="Loader2" size={48} className="mx-auto mb-4 opacity-50 animate-spin" />
                    <p>Loading emails...</p>
                  </div>
                ) : emails.length === 0 ? (
                  <div className="p-8 text-center text-muted-foreground">
                    <Icon name="Mail" size={48} className="mx-auto mb-4 opacity-50" />
                    <p>No emails yet</p>
                  </div>
                ) : (
                  <div className="divide-y">
                    {emails.map((email) => (
                      <div
                        key={email.id}
                        className={`p-5 hover:bg-[#F5F5F5] transition-colors cursor-pointer ${
                          !email.is_read && activeSection === 'inbox' ? 'bg-[#0066CC]/5' : ''
                        }`}
                        onClick={() => setSelectedEmail(email)}
                      >
                        <div className="flex items-start gap-4">
                          <div className="w-10 h-10 bg-gradient-to-br from-[#0066CC]/20 to-[#0066CC]/40 rounded-full flex items-center justify-center flex-shrink-0">
                            <Icon name="Mail" size={18} className="text-[#0066CC]" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between mb-1">
                              <p className={`font-semibold text-sm ${!email.is_read && activeSection === 'inbox' ? 'text-[#1A1A1A]' : 'text-muted-foreground'}`}>
                                {email.from || email.to}
                              </p>
                              <span className="text-xs text-muted-foreground">
                                {new Date(email.sent_at).toLocaleString()}
                              </span>
                            </div>
                            <p className={`text-sm mb-1 ${!email.is_read && activeSection === 'inbox' ? 'font-medium text-[#1A1A1A]' : 'text-muted-foreground'}`}>
                              {email.subject}
                            </p>
                            <p className="text-xs text-muted-foreground truncate">{email.body}</p>
                          </div>
                          {!email.is_read && activeSection === 'inbox' && (
                            <div className="w-2 h-2 bg-[#0066CC] rounded-full flex-shrink-0 mt-2"></div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </main>
        </div>
      </div>

      <Dialog open={showCompose} onOpenChange={setShowCompose}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>New Message</DialogTitle>
            <DialogDescription>Compose a new email</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="to">To</Label>
              <Input
                id="to"
                placeholder="recipient@skzry.ru"
                value={composeTo}
                onChange={(e) => setComposeTo(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="subject">Subject</Label>
              <Input
                id="subject"
                placeholder="Email subject"
                value={composeSubject}
                onChange={(e) => setComposeSubject(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="body">Message</Label>
              <Textarea
                id="body"
                placeholder="Write your message..."
                rows={8}
                value={composeBody}
                onChange={(e) => setComposeBody(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Button 
                onClick={() => handleSendEmail(false)} 
                disabled={loading}
                className="bg-[#0066CC] hover:bg-[#0052A3]"
              >
                <Icon name="Send" size={16} className="mr-2" />
                {loading ? 'Sending...' : 'Send'}
              </Button>
              <Button 
                variant="outline" 
                onClick={() => handleSendEmail(true)} 
                disabled={loading}
              >
                Save Draft
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={!!selectedEmail} onOpenChange={() => setSelectedEmail(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedEmail?.subject}</DialogTitle>
            <DialogDescription>
              From: {selectedEmail?.from || selectedEmail?.to} • {selectedEmail && new Date(selectedEmail.sent_at).toLocaleString()}
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            <p className="whitespace-pre-wrap">{selectedEmail?.body}</p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
