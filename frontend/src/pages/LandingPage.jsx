import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, FileText, Bot, ArrowRight, CheckCircle2 } from 'lucide-react';

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Navbar */}
      <nav className="w-full bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 text-primary font-bold text-xl">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white">
              <span className="leading-none">AF</span>
            </div>
            AidFlow AI
          </div>
          <div className="flex gap-4">
            <Link to="/login" className="text-slate-600 hover:text-slate-900 font-medium px-4 py-2">
              Log in
            </Link>
            <Link to="/register" className="bg-primary text-white hover:bg-blue-700 font-medium px-5 py-2 rounded-lg transition-colors shadow-sm">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-20 text-center relative overflow-hidden">
        {/* Background decorative elements */}
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-blue-100/50 blur-3xl -z-10"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-100/50 blur-3xl -z-10"></div>

        <div className="max-w-4xl space-y-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-sm font-medium border border-blue-100 mb-4">
            <span className="flex h-2 w-2 rounded-full bg-blue-600"></span>
            Empowering Citizens with AI
          </div>
          
          <h1 className="text-5xl md:text-7xl font-extrabold text-slate-900 tracking-tight leading-tight">
            Discover Govt Schemes <br className="hidden md:block"/> 
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">You Deserve.</span>
          </h1>
          
          <p className="text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
            AidFlow uses advanced AI to instantly match your profile with welfare schemes, 
            extract data from your documents securely, and generate personalized application checklists.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <Link to="/register" className="inline-flex items-center justify-center gap-2 bg-primary text-white text-lg font-medium px-8 py-4 rounded-xl hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-500/30 transition-all transform hover:-translate-y-0.5">
              Check My Eligibility
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
          
          <div className="flex items-center justify-center gap-6 text-sm text-slate-500 pt-8 font-medium">
            <div className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500"/> 100% Free</div>
            <div className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500"/> Secure & Private</div>
            <div className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-green-500"/> AI-Powered</div>
          </div>
        </div>
      </main>

      {/* Feature Section */}
      <section className="bg-white py-24 border-t border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-12">
            
            <div className="flex flex-col items-center text-center space-y-4 p-6 rounded-2xl bg-slate-50 border border-slate-100 transition-transform hover:-translate-y-1">
              <div className="w-16 h-16 rounded-2xl bg-blue-100 text-blue-600 flex items-center justify-center shadow-inner">
                <ShieldCheck className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold text-slate-900">Rule-Based Eligibility</h3>
              <p className="text-slate-600">Our engine evaluates your profile against hundreds of scheme criteria to find exact matches.</p>
            </div>

            <div className="flex flex-col items-center text-center space-y-4 p-6 rounded-2xl bg-slate-50 border border-slate-100 transition-transform hover:-translate-y-1">
              <div className="w-16 h-16 rounded-2xl bg-indigo-100 text-indigo-600 flex items-center justify-center shadow-inner">
                <FileText className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold text-slate-900">Smart Document OCR</h3>
              <p className="text-slate-600">Upload Aadhaar, PAN, or Income certificates. Our AI automatically extracts fields to save you typing.</p>
            </div>

            <div className="flex flex-col items-center text-center space-y-4 p-6 rounded-2xl bg-slate-50 border border-slate-100 transition-transform hover:-translate-y-1">
              <div className="w-16 h-16 rounded-2xl bg-purple-100 text-purple-600 flex items-center justify-center shadow-inner">
                <Bot className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold text-slate-900">AI Checklists & Reminders</h3>
              <p className="text-slate-600">Get step-by-step application guidance and automated email reminders so you never miss a deadline.</p>
            </div>
            
          </div>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="bg-slate-900 py-8 text-center border-t border-slate-800">
        <p className="text-slate-400 font-medium">© 2026 AidFlow AI. Empowering Citizens through Technology.</p>
      </footer>
    </div>
  );
};

export default LandingPage;
