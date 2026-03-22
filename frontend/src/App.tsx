import { Routes, Route, Navigate } from 'react-router-dom'
import { Join } from './pages/candidate/Join'
import { Entry } from './pages/candidate/Entry'
import { Exam } from './pages/candidate/Exam'
import { Finish } from './pages/candidate/Finish'
import { ProctorLogin } from './pages/proctor/ProctorLogin'
import { ProctorSession } from './pages/proctor/ProctorSession'
import { ProctorReview } from './pages/proctor/ProctorReview'
import { ProctorSessions } from './pages/proctor/ProctorSessions'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/join" replace />} />
      <Route path="/join" element={<Join />} />
      <Route path="/entry" element={<Entry />} />
      <Route path="/exam/:sessionId" element={<Exam />} />
      <Route path="/finish/:sessionId" element={<Finish />} />
      <Route path="/proctor/login" element={<ProctorLogin />} />
      <Route path="/proctor/sessions" element={<ProctorSessions />} />
      <Route path="/proctor/session/:sessionId" element={<ProctorSession />} />
      <Route path="/proctor/review/:sessionId" element={<ProctorReview />} />
    </Routes>
  )
}
