import React, { useState } from 'react';
import { 
  Users, 
  User,
  Search, 
  Filter, 
  ShieldCheck, 
  AlertTriangle, 
  Layers, 
  Eye, 
  FileText, 
  X, 
  CheckCircle2, 
  Download,
  Key,
  Calendar,
  Sparkles
} from 'lucide-react';
import { EnrolledSubject, SubjectCategory } from '../../types';

interface IdentityGalleryModuleProps {
  subjects: EnrolledSubject[];
  onUpdateSubject: (updated: EnrolledSubject) => void;
  onNavigateToEnrollment: () => void;
}

export const IdentityGalleryModule: React.FC<IdentityGalleryModuleProps> = ({
  subjects,
  onUpdateSubject,
  onNavigateToEnrollment
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [showMaskedReference, setShowMaskedReference] = useState(false);
  const [inspectSubject, setInspectSubject] = useState<EnrolledSubject | null>(null);

  const filteredSubjects = subjects.filter((s) => {
    const matchesSearch = s.fullName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          s.badgeId.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          s.department.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCat = selectedCategory === 'ALL' || s.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  const handleDownloadIdentitySheet = (subj: EnrolledSubject) => {
    const sheetData = `================================================
AEGIS-MASK IDENTIFICATION DOSSIER
================================================
Subject ID: ${subj.id}
Full Name: ${subj.fullName}
Badge ID: ${subj.badgeId}
Category: ${subj.category}
Clearance Level: ${subj.clearanceLevel}
Department: ${subj.department}
Risk Rating: ${subj.riskRating}
Status: ${subj.status}
Enrolled Date: ${subj.enrolledDate}
Enrolled By: ${subj.enrolledBy}

Notes:
${subj.notes}

512-D Periocular Vector Sample:
[${subj.embeddingVectorPreview.join(', ')}]
================================================`;

    const blob = new Blob([sheetData], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Identity_Sheet_${subj.badgeId}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Title & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 font-mono uppercase">
              IDENTITY GALLERY DATABASE
            </h1>
            <p className="text-xs text-slate-500">
              Enrolled subjects, dual-view reference photos, and 512-D vector embeddings
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Masked vs Unmasked View Toggle */}
          <button
            onClick={() => setShowMaskedReference(!showMaskedReference)}
            className={`px-3.5 py-2 rounded-lg border text-xs font-mono font-bold flex items-center space-x-2 transition-all cursor-pointer ${
              showMaskedReference
                ? 'bg-purple-600 text-white border-purple-600 shadow-sm'
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Eye className={`w-4 h-4 ${showMaskedReference ? 'text-white' : 'text-purple-600'}`} />
            <span>{showMaskedReference ? 'View Unmasked Reference' : 'View Masked Reference'}</span>
          </button>

          <button
            onClick={onNavigateToEnrollment}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-mono text-xs font-bold rounded-lg shadow-sm cursor-pointer transition-colors"
          >
            + Enroll New Subject
          </button>
        </div>
      </div>

      {/* Search & Category Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by subject name, badge ID, department..."
            className="w-full bg-white border border-slate-200 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-600 font-mono shadow-sm"
          />
        </div>

        <div className="flex items-center space-x-1.5 overflow-x-auto text-xs font-mono">
          {['ALL', 'Employee', 'Contractor', 'VIP', 'Watchlist', 'Visitor'].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-2 rounded-lg border cursor-pointer whitespace-nowrap transition-colors ${
                selectedCategory === cat
                  ? 'bg-indigo-600 text-white border-indigo-600 font-bold shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Grid of Subject Cards */}
      {filteredSubjects.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center space-y-3 font-mono">
          <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center mx-auto border border-indigo-100">
            <Users className="w-6 h-6" />
          </div>
          <h3 className="text-slate-800 font-bold text-sm">NO ENROLLED SUBJECTS FOUND</h3>
          <p className="text-slate-500 text-xs max-w-md mx-auto">
            The identity gallery is currently empty. Click "+ Enroll New Subject" above to register personnel, or await backend synchronization.
          </p>
          <button
            onClick={onNavigateToEnrollment}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg cursor-pointer transition-colors"
          >
            + Enroll First Subject Now
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSubjects.map((subj) => (
            <div
              key={subj.id}
              className={`p-4 bg-white border rounded-xl space-y-3 relative group transition-all shadow-sm ${
                subj.riskRating === 'Critical'
                  ? 'border-rose-300 bg-rose-50/20'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              {/* Risk Badge */}
              <div className="flex justify-between items-start">
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                  subj.category === 'Watchlist'
                    ? 'bg-rose-50 text-rose-700 border border-rose-200'
                    : subj.category === 'VIP'
                    ? 'bg-purple-50 text-purple-700 border border-purple-200'
                    : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                }`}>
                  {subj.category}
                </span>

                <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                  subj.riskRating === 'Critical' ? 'bg-rose-600 text-white font-bold animate-pulse' : 'text-slate-500'
                }`}>
                  {subj.clearanceLevel}
                </span>
              </div>

              {/* Photo & Info */}
              <div className="flex items-center space-x-3">
                <div className="w-16 h-16 rounded-lg bg-slate-100 border border-slate-200 overflow-hidden flex-shrink-0 relative flex items-center justify-center">
                  {(showMaskedReference ? subj.maskedPhotoUrl : subj.unmaskedPhotoUrl) ? (
                    <img
                      src={showMaskedReference ? subj.maskedPhotoUrl : subj.unmaskedPhotoUrl}
                      alt={subj.fullName}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <User className="w-8 h-8 text-indigo-500/70" />
                  )}
                  <span className="absolute bottom-0 right-0 px-1 py-0.2 bg-black/70 text-[8px] font-mono text-white">
                    {showMaskedReference ? 'MASK' : 'RAW'}
                  </span>
                </div>

                <div className="space-y-0.5 overflow-hidden">
                  <h3 className="font-bold text-xs text-slate-900 truncate">{subj.fullName}</h3>
                  <p className="text-[11px] font-mono text-slate-500">{subj.badgeId}</p>
                  <p className="text-[10px] text-slate-400 truncate">{subj.department}</p>
                </div>
              </div>

              {/* Footer Buttons */}
              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs font-mono">
                <span className="text-[10px] text-slate-400">
                  Last seen: {subj.lastSeenLocation || 'Zone A'}
                </span>

                <button
                  onClick={() => setInspectSubject(subj)}
                  className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-indigo-600 font-semibold cursor-pointer transition-colors"
                >
                  Inspect Dossier →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Inspect Subject Modal */}
      {inspectSubject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden p-6 space-y-6">
            <div className="flex justify-between items-start border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900 font-mono">{inspectSubject.fullName}</h2>
                <p className="text-xs text-slate-500 font-mono">Badge: {inspectSubject.badgeId} • {inspectSubject.department}</p>
              </div>
              <button onClick={() => setInspectSubject(null)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Dual Photos Side-by-Side */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2 flex flex-col items-center justify-center min-h-[180px]">
                <span className="text-[10px] font-mono text-indigo-600 font-bold self-start">UNMASKED REFERENCE PHOTO</span>
                {inspectSubject.unmaskedPhotoUrl ? (
                  <img src={inspectSubject.unmaskedPhotoUrl} alt="Unmasked" className="w-full h-40 object-cover rounded border border-slate-200" />
                ) : (
                  <div className="w-full h-40 bg-slate-100 rounded border border-slate-200 flex items-center justify-center text-slate-400 font-mono text-xs">
                    No Photo Enrolled
                  </div>
                )}
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2 flex flex-col items-center justify-center min-h-[180px]">
                <span className="text-[10px] font-mono text-purple-600 font-bold self-start">MASKED REFERENCE PHOTO</span>
                {inspectSubject.maskedPhotoUrl ? (
                  <img src={inspectSubject.maskedPhotoUrl} alt="Masked" className="w-full h-40 object-cover rounded border border-slate-200" />
                ) : (
                  <div className="w-full h-40 bg-slate-100 rounded border border-slate-200 flex items-center justify-center text-slate-400 font-mono text-xs">
                    No Photo Enrolled
                  </div>
                )}
              </div>
            </div>

            {/* Notes & Vectors */}
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2 font-mono text-xs">
              <div className="text-slate-400 text-[10px] uppercase font-bold">PERIOCULAR EMBEDDING VECTOR PREVIEW</div>
              <div className="grid grid-cols-6 gap-1 text-[10px] text-indigo-600">
                {inspectSubject.embeddingVectorPreview.map((v, i) => (
                  <div key={i} className="p-1 bg-white border border-slate-200 rounded text-center">{v}</div>
                ))}
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-between items-center pt-2 border-t border-slate-100">
              <button
                onClick={() => handleDownloadIdentitySheet(inspectSubject)}
                className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-mono text-xs font-bold rounded-lg flex items-center space-x-2 cursor-pointer transition-colors"
              >
                <Download className="w-4 h-4" />
                <span>Download Official Dossier Sheet</span>
              </button>
              <button
                onClick={() => setInspectSubject(null)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-mono text-xs font-bold rounded-lg cursor-pointer transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
