import React, { useState, useRef } from 'react';
import { 
  UserPlus, 
  Camera, 
  Upload, 
  Scan, 
  CheckCircle2, 
  ShieldCheck, 
  Sparkles, 
  AlertCircle, 
  Cpu, 
  Check, 
  RefreshCw,
  Layers,
  FileText,
  BadgeCheck
} from 'lucide-react';
import { EnrolledSubject, SubjectCategory } from '../../types';

interface EnrollmentModuleProps {
  onAddSubject: (newSubject: EnrolledSubject) => void;
  onNavigateToGallery: () => void;
}

export const EnrollmentModule: React.FC<EnrollmentModuleProps> = ({
  onAddSubject,
  onNavigateToGallery
}) => {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [useWebcam, setUseWebcam] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Captured / Selected Photos
  const [unmaskedPhoto, setUnmaskedPhoto] = useState<string>('');
  const [maskedPhoto, setMaskedPhoto] = useState<string>('');

  // Metadata form
  const [fullName, setFullName] = useState('');
  const [badgeId, setBadgeId] = useState(`EMP-${Math.floor(1000 + Math.random() * 9000)}`);
  const [category, setCategory] = useState<SubjectCategory>('Employee');
  const [clearanceLevel, setClearanceLevel] = useState<EnrolledSubject['clearanceLevel']>('Level 2');
  const [department, setDepartment] = useState('Cybersecurity Ops');
  const [riskRating, setRiskRating] = useState<EnrolledSubject['riskRating']>('Low');
  const [notes, setNotes] = useState('Enrolled via Security Officer Portal with dual-photo mask vector verification.');

  // Scanning simulation state
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [generatedVector, setGeneratedVector] = useState<number[]>([]);

  // Start / Stop Webcam
  const handleToggleWebcam = async () => {
    if (useWebcam) {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach(track => track.stop());
      }
      setUseWebcam(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        setUseWebcam(true);
        setTimeout(() => {
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
        }, 300);
      } catch (err) {
        alert('Camera access unavailable or blocked in frame permissions. Please use sample photos or file upload.');
      }
    }
  };

  const handleCaptureFromWebcam = (photoType: 'unmasked' | 'masked') => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = 400;
    canvas.height = 400;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(videoRef.current, 0, 0, 400, 400);
      const dataUrl = canvas.toDataURL('image/jpeg');
      if (photoType === 'unmasked') setUnmaskedPhoto(dataUrl);
      else setMaskedPhoto(dataUrl);
    }
  };

  const handleSimulateExtractVector = () => {
    setIsAnalyzing(true);
    setAnalysisComplete(false);

    setTimeout(() => {
      // Generate synthetic 12-point feature weights for preview
      const vector = Array.from({ length: 12 }, () => parseFloat((Math.random() * 0.9 + 0.1).toFixed(2)));
      setGeneratedVector(vector);
      setIsAnalyzing(false);
      setAnalysisComplete(true);
    }, 1500);
  };

  const handleFinalEnrollment = () => {
    if (!fullName.trim()) {
      alert('Please enter the Subject Full Name.');
      return;
    }

    const newSubject: EnrolledSubject = {
      id: `sub-${Date.now()}`,
      fullName,
      badgeId,
      category,
      clearanceLevel,
      department,
      unmaskedPhotoUrl: unmaskedPhoto,
      maskedPhotoUrl: maskedPhoto,
      enrolledDate: new Date().toISOString().split('T')[0],
      enrolledBy: 'Officer J. Vance',
      status: 'Active',
      riskRating,
      notes,
      embeddingVectorPreview: generatedVector.length ? generatedVector : [0.88, 0.45, 0.92, 0.33, 0.76, 0.12, 0.84, 0.61, 0.29, 0.90, 0.48, 0.77]
    };

    onAddSubject(newSubject);
    alert(`Subject "${fullName}" successfully enrolled into AEGIS-MASK vector database!`);
    onNavigateToGallery();
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-100">
            <UserPlus className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 font-mono uppercase">
              SUBJECT ENROLLMENT WIZARD
            </h1>
            <p className="text-xs text-slate-500">
              Register personnel with dual-photo periocular mask vector signature
            </p>
          </div>
        </div>

        {/* Step Indicator */}
        <div className="flex items-center space-x-2 text-xs font-mono">
          {[
            { num: 1, label: 'Photos' },
            { num: 2, label: 'Feature Extraction' },
            { num: 3, label: 'Identity Metadata' }
          ].map((s) => (
            <div
              key={s.num}
              onClick={() => setStep(s.num as any)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border cursor-pointer transition-colors ${
                step === s.num
                  ? 'bg-indigo-600 text-white border-indigo-600 font-bold shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <span className={`w-4 h-4 rounded-full text-[10px] flex items-center justify-center font-bold ${
                step === s.num ? 'bg-indigo-700 text-white' : 'bg-slate-100 text-slate-600'
              }`}>
                {s.num}
              </span>
              <span>{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* STEP 1: Capture / Upload Photos */}
      {step === 1 && (
        <div className="space-y-6">
          <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div>
              <h3 className="text-sm font-bold text-slate-800 font-mono">STEP 1: CAPTURE / UPLOAD REFERENCE PHOTOS</h3>
              <p className="text-xs text-slate-500">Provide both unmasked and masked photos for dual-model alignment calibration.</p>
            </div>
            <button
              onClick={handleToggleWebcam}
              className="px-3.5 py-2 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-600 border border-indigo-200 text-xs font-mono font-bold flex items-center space-x-2 transition-colors cursor-pointer"
            >
              <Camera className="w-4 h-4" />
              <span>{useWebcam ? 'Close Live Webcam' : 'Use Live Webcam'}</span>
            </button>
          </div>

          {/* Live Webcam Feed if active */}
          {useWebcam && (
            <div className="p-4 bg-slate-900 border border-indigo-500 rounded-xl space-y-3">
              <div className="text-xs font-mono text-indigo-300 flex items-center justify-between">
                <span>LIVE CAMERA CAPTURE STREAM</span>
                <span className="text-emerald-400 font-bold">● ONLINE</span>
              </div>
              <div className="relative aspect-video max-w-md mx-auto bg-black rounded-lg overflow-hidden border border-slate-800">
                <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
                <div className="absolute inset-x-0 bottom-3 flex justify-center space-x-3 px-4">
                  <button
                    onClick={() => handleCaptureFromWebcam('unmasked')}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-mono font-bold cursor-pointer shadow"
                  >
                    Set as Unmasked Photo
                  </button>
                  <button
                    onClick={() => handleCaptureFromWebcam('masked')}
                    className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded text-xs font-mono font-bold cursor-pointer shadow"
                  >
                    Set as Masked Photo
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Dual Photo Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Unmasked Reference */}
            <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-mono font-bold text-slate-800">UNMASKED REFERENCE PHOTO</span>
                <span className="text-[10px] text-indigo-600 font-mono bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                  Full Facial Features
                </span>
              </div>
              <div className="aspect-square bg-slate-100 rounded-lg overflow-hidden border border-slate-200 relative group flex items-center justify-center">
                {unmaskedPhoto ? (
                  <>
                    <img src={unmaskedPhoto} alt="Unmasked" className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-slate-900/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-2">
                      <label className="px-3 py-1.5 bg-indigo-600 text-white text-xs font-mono rounded font-bold cursor-pointer hover:bg-indigo-500 shadow">
                        Replace Photo
                        <input 
                          type="file" 
                          accept="image/*" 
                          className="hidden" 
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) setUnmaskedPhoto(URL.createObjectURL(file));
                          }}
                        />
                      </label>
                    </div>
                  </>
                ) : (
                  <label className="flex flex-col items-center justify-center w-full h-full cursor-pointer hover:bg-slate-200/50 transition-colors p-4 text-center">
                    <Upload className="w-8 h-8 text-indigo-500 mb-2" />
                    <span className="text-xs font-bold text-slate-700">Upload Unmasked Photo</span>
                    <span className="text-[10px] text-slate-400 mt-1">PNG, JPG or WEBP</span>
                    <input 
                      type="file" 
                      accept="image/*" 
                      className="hidden" 
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) setUnmaskedPhoto(URL.createObjectURL(file));
                      }}
                    />
                  </label>
                )}
              </div>
            </div>

            {/* Masked Reference */}
            <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-mono font-bold text-slate-800">MASKED REFERENCE PHOTO</span>
                <span className="text-[10px] text-purple-600 font-mono bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                  Periocular Focus
                </span>
              </div>
              <div className="aspect-square bg-slate-100 rounded-lg overflow-hidden border border-slate-200 relative group flex items-center justify-center">
                {maskedPhoto ? (
                  <>
                    <img src={maskedPhoto} alt="Masked" className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-slate-900/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-2">
                      <label className="px-3 py-1.5 bg-purple-600 text-white text-xs font-mono rounded font-bold cursor-pointer hover:bg-purple-500 shadow">
                        Replace Photo
                        <input 
                          type="file" 
                          accept="image/*" 
                          className="hidden" 
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) setMaskedPhoto(URL.createObjectURL(file));
                          }}
                        />
                      </label>
                    </div>
                  </>
                ) : (
                  <label className="flex flex-col items-center justify-center w-full h-full cursor-pointer hover:bg-slate-200/50 transition-colors p-4 text-center">
                    <Upload className="w-8 h-8 text-purple-500 mb-2" />
                    <span className="text-xs font-bold text-slate-700">Upload Masked Photo</span>
                    <span className="text-[10px] text-slate-400 mt-1">PNG, JPG or WEBP</span>
                    <input 
                      type="file" 
                      accept="image/*" 
                      className="hidden" 
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) setMaskedPhoto(URL.createObjectURL(file));
                      }}
                    />
                  </label>
                )}
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={() => {
                setStep(2);
                handleSimulateExtractVector();
              }}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-mono text-xs font-bold rounded-lg shadow-sm cursor-pointer flex items-center space-x-2"
            >
              <span>Next: Extract Feature Vector →</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: Periocular Feature Extraction */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
            <h3 className="text-sm font-bold text-slate-800 font-mono">STEP 2: PERIOCULAR VECTOR EXTRACTION</h3>
            <p className="text-xs text-slate-500">Generates deep ResNet-102 embeddings focused on forehead, eyebrow ridge, and eye line.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Visual Alignment Box */}
            <div className="p-4 bg-slate-900 rounded-xl border border-indigo-500/30 relative overflow-hidden space-y-3">
              <div className="text-xs font-mono text-indigo-300 font-bold flex items-center justify-between">
                <span>FACIAL LANDMARK ALIGNMENT</span>
                {isAnalyzing && <span className="text-yellow-400 animate-pulse">EXTRACTING...</span>}
              </div>

              <div className="relative aspect-square max-w-xs mx-auto rounded-lg overflow-hidden border border-slate-800">
                <img src={maskedPhoto} alt="Masked" className="w-full h-full object-cover" />
                {/* Overlay Landmark Box */}
                <div className="absolute top-[20%] left-[25%] w-[50%] h-[35%] border-2 border-indigo-400 rounded bg-indigo-500/10 p-1 flex flex-col justify-between">
                  <div className="flex justify-between text-[8px] font-mono text-indigo-200 font-bold">
                    <span>EYE LINE: 128px</span>
                    <span>NOSE BRIDGE: OK</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Feature Weights Graph */}
            <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-4">
              <h4 className="text-xs font-mono font-bold text-slate-800">
                GENERATED 512-D PERIOCULAR EMBEDDINGS (SAMPLE WEIGHTS)
              </h4>

              {isAnalyzing ? (
                <div className="py-12 flex flex-col items-center justify-center space-y-3 text-xs font-mono text-indigo-600">
                  <RefreshCw className="w-8 h-8 animate-spin text-indigo-600" />
                  <span>Computing Mask-Robust Embedding Vectors...</span>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="grid grid-cols-3 gap-2 font-mono text-[11px]">
                    {generatedVector.map((val, idx) => (
                      <div key={idx} className="p-2 rounded bg-slate-50 border border-slate-200 text-slate-800">
                        <div className="text-[9px] text-slate-400">DIM #{idx + 1}</div>
                        <div className="font-bold text-indigo-600">{val}</div>
                      </div>
                    ))}
                  </div>

                  <div className="p-3 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-mono flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>Vector signature validated against 0 duplicate identities in system!</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-between">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2 bg-slate-100 text-slate-700 font-mono text-xs font-bold rounded-lg hover:bg-slate-200 cursor-pointer"
            >
              ← Back to Photos
            </button>
            <button
              disabled={isAnalyzing}
              onClick={() => setStep(3)}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-mono text-xs font-bold rounded-lg shadow-sm cursor-pointer"
            >
              Next: Identity Metadata →
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Identity Metadata Form */}
      {step === 3 && (
        <div className="space-y-6">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-sm font-bold text-slate-800 font-mono">STEP 3: PERSONNEL & RISK METADATA</h3>
            <p className="text-xs text-slate-500">Complete subject clearance credentials and access tags.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div>
              <label className="block text-slate-500 mb-1">FULL NAME *</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Commander Robert Vance"
                className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-slate-900 focus:outline-none focus:border-indigo-600"
              />
            </div>

            <div>
              <label className="block text-slate-500 mb-1">BADGE / ID NUMBER</label>
              <input
                type="text"
                value={badgeId}
                onChange={(e) => setBadgeId(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-slate-900 focus:outline-none focus:border-indigo-600"
              />
            </div>

            <div>
              <label className="block text-slate-500 mb-1">SUBJECT CATEGORY</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as SubjectCategory)}
                className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-slate-900 focus:outline-none focus:border-indigo-600"
              >
                <option value="Employee">Employee</option>
                <option value="Contractor">Contractor</option>
                <option value="VIP">VIP</option>
                <option value="Watchlist">Watchlist</option>
                <option value="Restricted">Restricted</option>
                <option value="Visitor">Visitor</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-500 mb-1">CLEARANCE LEVEL</label>
              <select
                value={clearanceLevel}
                onChange={(e) => setClearanceLevel(e.target.value as any)}
                className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-slate-900 focus:outline-none focus:border-indigo-600"
              >
                <option value="Level 1">Level 1 (Standard Entry)</option>
                <option value="Level 2">Level 2 (Facilities & R&D)</option>
                <option value="Level 3">Level 3 (Vault Access)</option>
                <option value="Top Secret">Top Secret (Command Only)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-500 mb-1">DEPARTMENT / ORGANIZATION</label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-slate-900 focus:outline-none focus:border-indigo-600"
              />
            </div>

            <div>
              <label className="block text-slate-500 mb-1">EVALUATED RISK RATING</label>
              <select
                value={riskRating}
                onChange={(e) => setRiskRating(e.target.value as any)}
                className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-slate-900 focus:outline-none focus:border-indigo-600"
              >
                <option value="Low">Low Risk</option>
                <option value="Medium">Medium Risk</option>
                <option value="High">High Risk</option>
                <option value="Critical">Critical (Immediate Watchlist Flag)</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-slate-500 mb-1">SECURITY NOTES & ACCESS PERMITS</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-slate-900 focus:outline-none focus:border-indigo-600"
              />
            </div>
          </div>

          <div className="flex justify-between">
            <button
              onClick={() => setStep(2)}
              className="px-4 py-2 bg-slate-100 text-slate-700 font-mono text-xs font-bold rounded-lg hover:bg-slate-200 cursor-pointer"
            >
              ← Back to Vector Extraction
            </button>
            <button
              onClick={handleFinalEnrollment}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-mono text-xs font-bold rounded-lg shadow-sm cursor-pointer flex items-center space-x-2"
            >
              <BadgeCheck className="w-4 h-4" />
              <span>Complete Enrollment & Commit to Gallery</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
