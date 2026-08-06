import React, { useState, useEffect } from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { CameraFeed } from '../components/specialized/CameraFeed';
import { CheckCircle2, ChevronRight, Camera, RefreshCcw, Check, XCircle } from 'lucide-react';
import { cn } from '../utils/cn';
import { useCameraStream, useRecognitionStream } from '../hooks/useWebSocket';
import { useEnrollPerson } from '../utils/api';

const steps = [
  "Capture Images",
  "Quality Verification",
  "Employee Information",
  "Review & Save"
];


const base64ToBlob = (base64: string, mimeType: string = 'image/jpeg'): Blob => {
  const byteCharacters = atob(base64);
  const byteArrays = [];
  for (let offset = 0; offset < byteCharacters.length; offset += 512) {
    const slice = byteCharacters.slice(offset, offset + 512);
    const byteNumbers = new Array(slice.length);
    for (let i = 0; i < slice.length; i++) {
      byteNumbers[i] = slice.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    byteArrays.push(byteArray);
  }
  return new Blob(byteArrays, { type: mimeType });
};

export const Enrollment: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  
  
  const { data: cameraStream, isConnected: isCameraConnected } = useCameraStream();
  const { data: recognitionStream } = useRecognitionStream();

  
  const [captures, setCaptures] = useState<string[]>([]);
  const [quality, setQuality] = useState({
    faceDetected: false,
    maskDetected: false,
    avgConfidence: 0
  });

  
  const [formData, setFormData] = useState({
    fullName: '',
    employeeId: '',
    department: 'Engineering'
  });

  
  const enrollMutation = useEnrollPerson();

  
  useEffect(() => {
    if (currentStep === 0 && recognitionStream) {
       setQuality({
         faceDetected: recognitionStream.verification_score > 0,
         maskDetected: recognitionStream.mask_status,
         avgConfidence: recognitionStream.verification_score
       });
    }
  }, [recognitionStream, currentStep]);

  const handleCapture = () => {
    if (cameraStream && captures.length < 5) {
      setCaptures(prev => [...prev, cameraStream.image_base64]);
    }
  };

  const handleReset = () => {
    setCaptures([]);
    setCurrentStep(0);
    setFormData({ fullName: '', employeeId: '', department: 'Engineering' });
    enrollMutation.reset();
  };

  const handleSubmit = () => {
    const blobs = captures.map(b64 => base64ToBlob(b64));
    enrollMutation.mutate({
      identity_id: formData.employeeId,
      name: formData.fullName,
      files: blobs
    }, {
      onSuccess: () => {
         setCurrentStep(4);
      }
    });
  };

  const canProceed = () => {
    if (currentStep === 0) return captures.length === 5;
    if (currentStep === 1) return quality.faceDetected && !quality.maskDetected;
    if (currentStep === 2) return formData.fullName.length > 0 && formData.employeeId.length > 0;
    return true;
  };

  const handleNext = () => {
    if (currentStep === 3) {
      handleSubmit();
    } else {
      setCurrentStep(s => s + 1);
    }
  };

  return (
    <div className="h-full flex flex-col gap-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Identity Enrollment</h2>
          <p className="text-sm text-gray-600 mt-1">Guided workflow for registering new users into the system.</p>
        </div>
        
        {}
        <div className="flex items-center gap-2 text-sm font-medium">
          {steps.map((step, idx) => (
            <React.Fragment key={step}>
              <div className={cn(
                "flex items-center gap-1.5 px-3 py-1 rounded",
                idx === currentStep ? "bg-primary text-gray-900" : 
                idx < currentStep ? "text-success" : "text-gray-500"
              )}>
                {idx < currentStep && <CheckCircle2 size={16} />}
                {idx + 1}. {step}
              </div>
              {idx < steps.length - 1 && <ChevronRight size={16} className="text-gray-600" />}
            </React.Fragment>
          ))}
        </div>
      </div>

      <Card className="flex-1 flex flex-col relative overflow-hidden">
        {}
        <div className="flex-1 p-6 flex items-center justify-center bg-secondary/30">
          
          {currentStep === 0 && (
            <div className="w-full max-w-4xl flex gap-6 h-full">
              <div className="flex-[2] flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">Live Capture</h3>
                  <div className="flex items-center gap-2 text-xs text-gray-600">
                     <span className={cn("w-2 h-2 rounded-full", isCameraConnected ? "bg-success" : "bg-danger")}></span>
                     {isCameraConnected ? "Camera Connected" : "Camera Disconnected"}
                  </div>
                </div>
                <div className="flex-1 border border-gray-300 bg-black rounded-md overflow-hidden relative">
                  <CameraFeed 
                    className="w-full h-full border-none rounded-none" 
                    isOnline={isCameraConnected} 
                    streamUrl={cameraStream ? `data:image/jpeg;base64,${cameraStream.image_base64}` : undefined}
                  />
                  <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                    <div className="w-64 h-80 border-2 border-dashed border-primary/50 rounded-[40%] flex items-center justify-center relative">
                       <div className="absolute top-4 inset-x-0 text-center text-[10px] font-medium text-primary bg-black/50 py-1 px-3 rounded-full mx-auto w-fit uppercase tracking-wider">Align face within oval</div>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-600">Capture 5 varied angles (Front, Left, Right, Up, Down)</p>
                  <Button onClick={handleCapture} disabled={!isCameraConnected || captures.length >= 5}>
                    <Camera size={16} className="mr-2"/> Capture ({captures.length}/5)
                  </Button>
                </div>
              </div>
              <div className="flex-1 flex flex-col gap-4">
                <h3 className="text-lg font-medium text-gray-900">Live Quality</h3>
                <Card className="p-4 space-y-4 border-gray-200 bg-background">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-600">Face Detected</span>
                      <span className={quality.faceDetected ? "text-success" : "text-warning"}>
                        {quality.faceDetected ? "Yes" : "No"}
                      </span>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-600">Detection Confidence</span>
                      <span className="text-success">{(quality.avgConfidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-black rounded overflow-hidden">
                      <div className="h-full bg-success transition-all" style={{ width: `${quality.avgConfidence * 100}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-600">Mask Status</span>
                      <span className={quality.maskDetected ? "text-danger" : "text-success"}>
                        {quality.maskDetected ? "Mask Detected" : "Clear"}
                      </span>
                    </div>
                  </div>
                </Card>
                
                <div className="grid grid-cols-2 gap-2 mt-auto">
                  {[0,1,2,3,4].map(i => (
                    <div key={i} className={`aspect-square rounded border ${i < captures.length ? 'border-primary/50 p-0.5' : 'border-gray-300 border-dashed'} bg-secondary flex items-center justify-center overflow-hidden`}>
                      {i < captures.length ? (
                        <img src={`data:image/jpeg;base64,${captures[i]}`} className="w-full h-full object-cover bg-black"/>
                      ) : (
                        <span className="text-xs text-gray-600">{i + 1}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {currentStep === 1 && (
             <div className="text-center space-y-6 max-w-md w-full">
               <h3 className="text-xl text-gray-900">Quality Verification</h3>
               <div className="space-y-4 text-left bg-background p-6 rounded border border-gray-300">
                 <div className="flex items-center justify-between">
                   <span className="text-gray-700">Minimum 5 Captures</span>
                   {captures.length === 5 ? <Check size={18} className="text-success" /> : <XCircle size={18} className="text-danger" />}
                 </div>
                 <div className="flex items-center justify-between">
                   <span className="text-gray-700">Face Detected Continuously</span>
                   {quality.faceDetected ? <Check size={18} className="text-success" /> : <XCircle size={18} className="text-danger" />}
                 </div>
                 <div className="flex items-center justify-between">
                   <span className="text-gray-700">No Mask Detected</span>
                   {!quality.maskDetected ? <Check size={18} className="text-success" /> : <XCircle size={18} className="text-danger" />}
                 </div>
               </div>
               {(!quality.faceDetected || quality.maskDetected) && (
                 <p className="text-sm text-danger bg-danger/10 p-3 rounded border border-danger/20">
                   Quality checks failed. Please ensure your face is fully visible and not wearing a mask.
                 </p>
               )}
             </div>
          )}

          {currentStep === 2 && (
             <div className="w-full max-w-md space-y-4">
                <h3 className="text-xl text-gray-900 mb-6 text-center">Employee Information</h3>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Full Name</label>
                  <input 
                    type="text" 
                    value={formData.fullName}
                    onChange={e => setFormData(f => ({ ...f, fullName: e.target.value }))}
                    className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 focus:border-primary focus:outline-none" 
                    placeholder="e.g. Felix Architect"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Employee ID (Unique)</label>
                  <input 
                    type="text" 
                    value={formData.employeeId}
                    onChange={e => setFormData(f => ({ ...f, employeeId: e.target.value }))}
                    className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 focus:border-primary focus:outline-none" 
                    placeholder="e.g. EMP-9482"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Department</label>
                  <select 
                    value={formData.department}
                    onChange={e => setFormData(f => ({ ...f, department: e.target.value }))}
                    className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900 focus:border-primary focus:outline-none"
                  >
                     <option>Engineering</option>
                     <option>Security</option>
                     <option>Operations</option>
                     <option>Executive</option>
                  </select>
                </div>
             </div>
          )}

          {currentStep === 3 && (
             <div className="w-full max-w-md space-y-6 text-center">
               <h3 className="text-xl text-gray-900">Review & Submit</h3>
               <div className="flex gap-4 justify-center">
                  <div className="w-32 h-32 rounded border-2 border-primary overflow-hidden">
                    <img src={`data:image/jpeg;base64,${captures[0]}`} className="w-full h-full object-cover" />
                  </div>
               </div>
               <div className="bg-background border border-gray-300 p-4 rounded text-left space-y-2 text-sm">
                 <div className="flex justify-between"><span className="text-gray-600">Name:</span><span className="text-gray-900 font-medium">{formData.fullName}</span></div>
                 <div className="flex justify-between"><span className="text-gray-600">ID:</span><span className="text-gray-900 font-medium">{formData.employeeId}</span></div>
                 <div className="flex justify-between"><span className="text-gray-600">Department:</span><span className="text-gray-900 font-medium">{formData.department}</span></div>
                 <div className="flex justify-between"><span className="text-gray-600">Captures:</span><span className="text-success font-medium">5 Images</span></div>
               </div>
               
               {enrollMutation.isPending && (
                 <div className="flex flex-col items-center gap-3 pt-4">
                   <RefreshCcw className="animate-spin text-primary" />
                   <p className="text-sm text-gray-600">Extracting embeddings and saving to database...</p>
                 </div>
               )}
               
               {enrollMutation.isError && (
                 <div className="bg-danger/10 border border-danger/30 text-danger p-3 rounded text-sm text-left">
                   <strong>Enrollment Failed:</strong> {enrollMutation.error?.message}
                 </div>
               )}
             </div>
          )}
          
          {currentStep === 4 && (
            <div className="text-center space-y-6 max-w-md w-full">
              <CheckCircle2 size={64} className="text-success mx-auto" />
              <h3 className="text-2xl text-gray-900">Enrollment Successful</h3>
              <p className="text-sm text-gray-600">
                Identity <strong className="text-gray-900">{formData.fullName} ({formData.employeeId})</strong> has been successfully enrolled into the FAISS index.
              </p>
              <div className="pt-4 flex gap-4 justify-center">
                <Button onClick={handleReset}>Enroll Another Person</Button>
              </div>
            </div>
          )}

        </div>

        {}
        {currentStep < 4 && (
          <div className="p-4 border-t border-gray-200 bg-background flex justify-between">
            <Button variant="ghost" onClick={() => setCurrentStep(Math.max(0, currentStep - 1))} disabled={currentStep === 0 || enrollMutation.isPending}>Back</Button>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleReset} disabled={enrollMutation.isPending}>Reset</Button>
              <Button 
                 onClick={handleNext}
                 disabled={!canProceed() || enrollMutation.isPending}
              >
                 {currentStep === 3 ? "Submit Enrollment" : "Next Step"}
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

