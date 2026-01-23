import { useState, useEffect } from 'react'
import { ArrowLeft, ChevronRight, MessageCircle, Mail, ExternalLink } from 'lucide-react'
import { fetchAPI } from '../../services/api'

interface FAQ {
  q: string
  a: string
}

interface HelpViewProps {
  onBack: () => void
}

export function HelpView({ onBack }: HelpViewProps) {
  const [faqs, setFaqs] = useState<FAQ[]>([])
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadFaqs = async () => {
      try {
        const data = await fetchAPI<FAQ[]>('/v1/support/faq')
        setFaqs(data)
      } catch {
        // Use default FAQs
        setFaqs([
          { q: 'How do I earn exclusives?', a: 'Visit a charger within our network and browse nearby merchants. When you activate an exclusive offer, you have 30 minutes to visit the merchant and redeem it.' },
          { q: 'What happens if I don\'t use my exclusive?', a: 'Exclusives expire after 30 minutes. If you don\'t use it, it will be released for other drivers.' },
          { q: 'How do I contact support?', a: 'You can email us at support@nerava.network or use the contact options above.' }
        ])
      } finally {
        setLoading(false)
      }
    }
    loadFaqs()
  }, [])

  return (
    <div className="h-[100dvh] flex flex-col bg-white">
      <header className="px-5 h-[60px] flex items-center border-b border-[#E4E6EB]">
        <button onClick={onBack} className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="ml-4 text-lg font-medium">Help & Support</h1>
      </header>

      <div className="flex-1 overflow-y-auto">
        {/* Contact Options */}
        <div className="p-5 border-b border-[#E4E6EB]">
          <h2 className="text-sm font-medium text-[#65676B] uppercase mb-4">Contact Us</h2>
          <div className="space-y-3">
            <a
              href="mailto:support@nerava.network"
              className="flex items-center p-4 bg-[#F7F8FA] rounded-xl"
            >
              <Mail className="w-5 h-5 text-[#1877F2] mr-3" />
              <div className="flex-1">
                <p className="font-medium text-[#050505]">Email Support</p>
                <p className="text-sm text-[#65676B]">support@nerava.network</p>
              </div>
              <ExternalLink className="w-4 h-4 text-[#65676B]" />
            </a>
            <a
              href="https://nerava.network/help"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center p-4 bg-[#F7F8FA] rounded-xl"
            >
              <MessageCircle className="w-5 h-5 text-green-500 mr-3" />
              <div className="flex-1">
                <p className="font-medium text-[#050505]">Help Center</p>
                <p className="text-sm text-[#65676B]">Browse articles and guides</p>
              </div>
              <ExternalLink className="w-4 h-4 text-[#65676B]" />
            </a>
          </div>
        </div>

        {/* FAQs */}
        <div className="p-5">
          <h2 className="text-sm font-medium text-[#65676B] uppercase mb-4">
            Frequently Asked Questions
          </h2>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin w-6 h-6 border-2 border-[#1877F2] border-t-transparent rounded-full" />
            </div>
          ) : (
            <div className="space-y-2">
              {faqs.map((faq, index) => (
                <div key={index} className="border border-[#E4E6EB] rounded-xl overflow-hidden">
                  <button
                    onClick={() => setExpandedFaq(expandedFaq === index ? null : index)}
                    className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50"
                  >
                    <span className="font-medium text-[#050505] pr-4">{faq.q}</span>
                    <ChevronRight
                      className={`w-5 h-5 text-[#65676B] transition-transform flex-shrink-0 ${
                        expandedFaq === index ? 'rotate-90' : ''
                      }`}
                    />
                  </button>
                  {expandedFaq === index && (
                    <div className="px-4 pb-4 text-[#65676B] text-sm">
                      {faq.a}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}


