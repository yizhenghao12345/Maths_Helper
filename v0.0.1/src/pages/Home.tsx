import { useNavigate } from 'react-router-dom'
import { Brain, Lightbulb, Target } from 'lucide-react'

const Home = () => {
  const navigate = useNavigate()

  const features = [
    {
      icon: Brain,
      title: '可视化思维导图',
      description: '将解题过程可视化展示,让你看清每一步的思考逻辑',
      color: 'from-blue-500 to-cyan-400',
    },
    {
      icon: Lightbulb,
      title: 'AI引导推演',
      description: '通过苏格拉底式提问,引导你自主思考,培养解题思维',
      color: 'from-amber-500 to-orange-400',
    },
    {
      icon: Target,
      title: '温和纠错机制',
      description: '选择错误路径时,AI会温和地提示原因,帮助你纠正思路',
      color: 'from-green-500 to-emerald-400',
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-cyan-50">
      <header className="px-8 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Brain className="w-8 h-8 text-blue-600" />
          <span className="text-xl font-bold text-gray-800">数学思维助手</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-8 py-16">
        <section className="text-center mb-20">
          <h1 className="text-5xl font-bold text-gray-900 mb-6 animate-fade-in">
            告别"一看就懂,一做就错"
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-10">
            通过可视化思维节点和互动式引导,从根源上培养数学逻辑能力
          </p>
          <button
            onClick={() => navigate('/input')}
            className="px-8 py-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-lg font-semibold rounded-full shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300 pulse-animation"
          >
            开始使用
          </button>
        </section>

        <section className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white rounded-2xl p-8 shadow-md hover:shadow-xl transform hover:-translate-y-2 transition-all duration-300"
            >
              <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6`}>
                <feature.icon className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-3">
                {feature.title}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </section>
      </main>
    </div>
  )
}

export default Home
