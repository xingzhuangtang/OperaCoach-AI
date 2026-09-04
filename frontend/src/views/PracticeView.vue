<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { synthesizeSpeech, playAudio, stopAudio } from '@/utils/tts'

const router = useRouter()

interface PracticeItem {
  area: string
  tip: string
}

interface ChenziData {
  char: string
  pinyin: string
  desc: string
  keywords: string
  practice: PracticeItem[]
}

const CHENZI_DATA: ChenziData[] = [
  {
    char: '啊', pinyin: 'ā', desc: '练通道与打开', keywords: '宽广 通畅 宏大 垂直 敞亮',
    practice: [
      { area: '嗓子', tip: '打哈欠状态起音，喉头自然下降，软腭上提，感受喉咙完全打开' },
      { area: '胸腔', tip: '手按胸口，发"啊——"长音，感受胸腔震动，声音从上往下沉' },
      { area: '气息', tip: '吸气时肋骨扩张，呼气时保持打开状态，匀速发"啊"持续15秒以上' },
      { area: '科班', tip: '蛤蟆气：鼻吸腹鼓，屏息2秒，唇缝"嘶——"出气30秒，腹部撑住慢收' },
    ],
  },
  {
    char: '哎', pinyin: 'ái', desc: '练靠前与明亮', keywords: '清脆 鲜活 靠前 积极',
    practice: [
      { area: '嗓子', tip: '嘴角微抬，声音集中在口腔前部，像打招呼一样自然地发"哎"' },
      { area: '鼻腔', tip: '感受声音从硬腭前方透出，鼻尖有轻微震动感' },
      { area: '气息', tip: '短促有力地发"哎！哎！哎！"，每次配合腹部弹跳，练声音的爆发力' },
      { area: '科班', tip: '念"天""下"等字时，字头轻咬，迅速滑向韵母，尾音归鼻腔，练尖团字' },
    ],
  },
  {
    char: '咦', pinyin: 'yí', desc: '练高位置与面罩共鸣', keywords: '穿透 鲜亮 眉心震',
    practice: [
      { area: '鼻腔', tip: '发"咦"时想象声音从眉心穿出，用手指轻点眉心感受震动' },
      { area: '嗓子', tip: '声音细而集中，像一根线从头顶穿出，不要压喉' },
      { area: '气息', tip: '小腹微收支撑，气流细而稳，发"咦——"由弱渐强再渐弱' },
      { area: '科班', tip: '咬着后槽牙发"咦"，意念绕过后脑勺再从眉心出，捏鼻不闷则鼻腔通' },
    ],
  },
  {
    char: '呦', pinyin: 'yōu', desc: '练咽腔打开与声音竖立', keywords: '圆润 立体 空间 包满',
    practice: [
      { area: '嗓子', tip: '嘴唇圆突，咽腔竖起，像含着一口水发"呦"，保持口腔内空间' },
      { area: '胸腔', tip: '声音从上往下"坐"，同时保持咽腔的竖立感，上下贯通' },
      { area: '气息', tip: '深吸到腰腹，发"呦——"时腹部缓慢内收，声音保持圆润不扁' },
      { area: '科班', tip: '练"橄榄腔"：字头轻、字腹满、字尾收鼻腔，形成枣弧形力度' },
    ],
  },
  {
    char: '呜', pinyin: 'wū', desc: '练喉头稳定与混声/掩盖', keywords: '温暖 深厚 暗 包裹感',
    practice: [
      { area: '嗓子', tip: '双唇前突成小圆形，喉头放松下沉，发"呜"时摸喉结应无明显上提' },
      { area: '胸腔', tip: '手放胸口感受深沉的共鸣，声音像从胸腔底部发出' },
      { area: '腹腔', tip: '双手叉腰，吸气时腰部扩张，发"呜——"时腰部缓慢回收，练气息的深度支撑' },
      { area: '科班', tip: '脑后音哼鸣：闭嘴发"嗯——"，意念砸向后脑枕骨，做滑梯音从低到高再到低' },
    ],
  },
  {
    char: '啦', pinyin: 'lā', desc: '练舌头灵活与声音弹跳', keywords: '弹跳 灵活 颗粒 轻快',
    practice: [
      { area: '嗓子', tip: '舌尖轻弹上齿龈，发"啦"时声音要轻快有弹性，不要拖泥带水' },
      { area: '腹腔', tip: '每个"啦"配合腹部一次弹跳，像笑一样"哈-哈-哈"的感觉' },
      { area: '气息', tip: '快速连续发"啦啦啦啦"，每音之间腹部弹动，练气息的灵活控制' },
      { area: '科班', tip: '数豆子法：深吸气念"天下不用"等字，一口气念完一遍，练到能念4遍' },
    ],
  },
  {
    char: '嘻', pinyin: 'xī', desc: '练气息下沉与轻巧高位置', keywords: '轻巧 叹气 弱声 集中',
    practice: [
      { area: '腹腔', tip: '先叹一口气感受气息沉到小腹，然后顺势发"嘻"，声音轻而不虚' },
      { area: '鼻腔', tip: '声音集中在鼻腔高位，像轻声说秘密一样，集中成一个小点' },
      { area: '气息', tip: '发"嘻——"时保持腹部支撑，声音从强到弱再到强，练气息的持久控制' },
      { area: '科班', tip: '收功必做：搓热双手揉天突穴、迎香穴，喝温水，发极弱气泡音按摩声带' },
    ],
  },
]

type Stage = 'select' | 'guide' | 'practice' | 'done'

const stage = ref<Stage>('select')
const selectedMode = ref<'daily' | 'custom'>('daily')
const selectedChars = ref<Set<string>>(new Set())
const timerDuration = ref(15)

const sessionQueue = ref<{ char: ChenziData; practice: PracticeItem }[]>([])
const currentIndex = ref(0)
const timeRemaining = ref(15)
const timerInterval = ref<number | null>(null)
const isPlayingDemo = ref(false)
const isSpeaking = ref(false)

const currentItem = computed(() => sessionQueue.value[currentIndex.value])
const totalItems = computed(() => sessionQueue.value.length)
const progressPercent = computed(() =>
  totalItems.value > 0 ? (currentIndex.value / totalItems.value) * 100 : 0
)
const timerPercent = computed(() =>
  timerDuration.value > 0 ? (timeRemaining.value / timerDuration.value) * 100 : 0
)

onUnmounted(() => {
  cleanup()
})

function cleanup() {
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
    timerInterval.value = null
  }
  stopAudio()
}

function toggleChar(char: string) {
  const s = new Set(selectedChars.value)
  if (s.has(char)) s.delete(char)
  else s.add(char)
  selectedChars.value = s
}

function startSession() {
  const chars = selectedMode.value === 'daily'
    ? CHENZI_DATA
    : CHENZI_DATA.filter(c => selectedChars.value.has(c.char))

  if (chars.length === 0) return

  const queue: { char: ChenziData; practice: PracticeItem }[] = []
  for (const c of chars) {
    for (const p of c.practice) {
      queue.push({ char: c, practice: p })
    }
  }

  sessionQueue.value = queue
  currentIndex.value = 0
  stage.value = 'guide'
  speakCurrentInstructions()
}

async function speakCurrentInstructions() {
  if (!currentItem.value || isSpeaking.value) return
  const { char, practice } = currentItem.value
  const text = `${char.char}，${char.pinyin}。练习部位：${practice.area}。${practice.tip}`
  isSpeaking.value = true
  try {
    const url = await synthesizeSpeech(text, 'longxiaochun')
    await playAudio(url)
  } catch {
    // ignore
  } finally {
    isSpeaking.value = false
  }
}

function buildDemoText(char: ChenziData, practice: PracticeItem): string {
  return `${char.char}，${char.pinyin}。${practice.tip}。` +
    `好，深吸一口气，丹田撑住。` +
    `来，跟我们一起发，${char.char}——。` +
    `再来一次，${char.char}——。保持住，感受${practice.area}的共鸣。` +
    `很好，慢慢收住，放松。`
}

async function playDemo() {
  if (!currentItem.value || isPlayingDemo.value) return
  isPlayingDemo.value = true
  try {
    const { char, practice } = currentItem.value
    const text = buildDemoText(char, practice)
    const url = await synthesizeSpeech(text, 'longxiaochun')
    await playAudio(url)
  } catch {
    // ignore
  } finally {
    isPlayingDemo.value = false
  }
}

function startPractice() {
  timeRemaining.value = timerDuration.value
  stage.value = 'practice'

  const { char, practice } = currentItem.value
  const text = buildDemoText(char, practice)
  synthesizeSpeech(text, 'longxiaochun')
    .then(url => playAudio(url))
    .catch(() => {})

  const startTime = Date.now()
  timerInterval.value = window.setInterval(() => {
    const elapsed = (Date.now() - startTime) / 1000
    timeRemaining.value = Math.max(0, timerDuration.value - elapsed)

    if (timeRemaining.value <= 0) {
      finishExercise()
    }
  }, 100)
}

function finishExercise() {
  cleanup()
  if (currentIndex.value < totalItems.value - 1) {
    currentIndex.value++
    stage.value = 'guide'
    speakCurrentInstructions()
  } else {
    stage.value = 'done'
  }
}

function skipExercise() {
  cleanup()
  finishExercise()
}

function goBack() {
  cleanup()
  router.push('/hub')
}

function resetToSelect() {
  cleanup()
  stage.value = 'select'
}

const circumference = 2 * Math.PI * 90
</script>

<template>
  <div class="practice-container">
    <header class="practice-header">
      <button class="back-btn" @click="goBack">← 返回</button>
      <div class="header-brand">
        <span class="brand-name">影子戏</span>
        <span class="brand-sep">·</span>
        <span class="brand-section">AI陪练</span>
      </div>
      <div class="header-spacer"></div>
    </header>

    <main class="practice-main">
      <!-- 选择阶段 -->
      <div v-if="stage === 'select'" class="select-stage fade-in">
        <h2 class="stage-title">每日发声练习</h2>
        <p class="stage-subtitle">结合七个衬字，系统训练嗓子、气息、共鸣</p>

        <div class="mode-cards">
          <div
            class="mode-card"
            :class="{ active: selectedMode === 'daily' }"
            @click="selectedMode = 'daily'"
          >
            <div class="mode-icon">日</div>
            <h3>每日训练</h3>
            <p>全部7个衬字，21项练习</p>
          </div>
          <div
            class="mode-card"
            :class="{ active: selectedMode === 'custom' }"
            @click="selectedMode = 'custom'"
          >
            <div class="mode-icon">选</div>
            <h3>自定义选择</h3>
            <p>选择要练习的衬字</p>
          </div>
        </div>

        <div v-if="selectedMode === 'custom'" class="char-selector">
          <div
            v-for="c in CHENZI_DATA"
            :key="c.char"
            class="char-btn"
            :class="{ selected: selectedChars.has(c.char) }"
            @click="toggleChar(c.char)"
          >
            <span class="char-label">{{ c.char }}</span>
            <span class="char-pinyin">{{ c.pinyin }}</span>
          </div>
        </div>

        <div class="duration-control">
          <span class="duration-label">每项练习时长</span>
          <div class="duration-slider">
            <input type="range" min="5" max="60" step="5" v-model.number="timerDuration" />
            <span class="duration-value">{{ timerDuration }}秒</span>
          </div>
        </div>

        <button class="start-btn" @click="startSession">
          开始练习
        </button>
      </div>

      <!-- 指导阶段 -->
      <div v-else-if="stage === 'guide'" class="guide-stage fade-in">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <div class="progress-text">{{ currentIndex + 1 }} / {{ totalItems }}</div>

        <div class="chenzi-display">
          <div class="chenzi-char">{{ currentItem?.char.char }}</div>
          <div class="chenzi-pinyin">({{ currentItem?.char.pinyin }})</div>
          <div class="chenzi-desc">{{ currentItem?.char.desc }}</div>
          <div class="chenzi-keywords">{{ currentItem?.char.keywords }}</div>
        </div>

        <div class="practice-instruction">
          <div class="instruction-area">{{ currentItem?.practice.area }}</div>
          <div class="instruction-tip">{{ currentItem?.practice.tip }}</div>
        </div>

        <div class="action-buttons">
          <button class="action-btn demo-btn" :disabled="isPlayingDemo" @click="playDemo">
            {{ isPlayingDemo ? '播放中...' : '播放示范音' }}
          </button>
          <button class="action-btn speak-btn" :disabled="isSpeaking" @click="speakCurrentInstructions">
            {{ isSpeaking ? '朗读中...' : '朗读指导' }}
          </button>
          <button class="action-btn start-practice-btn" @click="startPractice">
            开始练习
          </button>
        </div>

        <button class="text-btn" @click="resetToSelect">重新选择</button>
      </div>

      <!-- 练习阶段 -->
      <div v-else-if="stage === 'practice'" class="practice-stage">
        <div class="timer-wrapper">
          <svg class="timer-svg" viewBox="0 0 200 200">
            <circle class="timer-bg" cx="100" cy="100" r="90" />
            <circle
              class="timer-progress"
              cx="100" cy="100" r="90"
              :stroke-dasharray="circumference"
              :stroke-dashoffset="circumference * (1 - timerPercent / 100)"
            />
          </svg>
          <div class="timer-center">
            <div class="timer-char">{{ currentItem?.char.char }}</div>
            <div class="timer-count">{{ Math.ceil(timeRemaining) }}</div>
          </div>
        </div>

        <div class="timer-hint">
          <span class="hint-area">{{ currentItem?.practice.area }}</span>
          <span class="hint-tip">{{ currentItem?.practice.tip }}</span>
        </div>

        <button class="text-btn skip-btn" @click="skipExercise">跳过</button>
      </div>

      <!-- 完成阶段 -->
      <div v-else-if="stage === 'done'" class="done-stage fade-in">
        <div class="done-icon">功</div>
        <h2 class="done-title">今日练习完成</h2>
        <p class="done-subtitle">坚持每日练习，嗓音日渐精进</p>
        <div class="done-stats">
          <div class="stat-item">
            <span class="stat-num">{{ totalItems }}</span>
            <span class="stat-label">练习项</span>
          </div>
          <div class="stat-item">
            <span class="stat-num">{{ timerDuration }}s</span>
            <span class="stat-label">每项时长</span>
          </div>
        </div>
        <button class="start-btn" @click="resetToSelect">再来一轮</button>
        <button class="text-btn" @click="goBack">返回首页</button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.practice-container {
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

.practice-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  background: rgba(26, 26, 46, 0.85);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(184, 134, 11, 0.12);
}

.back-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  cursor: pointer;
  letter-spacing: 1px;
  padding: 6px 12px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.back-btn:hover {
  color: #b8860b;
  background: rgba(184, 134, 11, 0.08);
}

.header-brand {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.brand-name {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #b8860b 0%, #daa520 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 3px;
}

.brand-sep { color: rgba(184, 134, 11, 0.3); font-size: 16px; }
.brand-section { color: rgba(255, 255, 255, 0.5); font-size: 14px; letter-spacing: 2px; }
.header-spacer { width: 100px; }

.practice-main {
  max-width: 700px;
  margin: 0 auto;
  padding: 40px 32px;
}

.fade-in {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 选择阶段 */
.stage-title {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #b8860b 0%, #daa520 50%, #b8860b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 4px;
  text-align: center;
  margin-bottom: 8px;
}

.stage-subtitle {
  color: rgba(255, 255, 255, 0.35);
  font-size: 14px;
  letter-spacing: 2px;
  text-align: center;
  margin-bottom: 40px;
}

.mode-cards {
  display: flex;
  gap: 24px;
  justify-content: center;
  margin-bottom: 32px;
}

.mode-card {
  width: 200px;
  padding: 28px 20px;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border-radius: 10px;
  border: 1px solid rgba(184, 134, 11, 0.12);
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.mode-card:hover {
  border-color: rgba(184, 134, 11, 0.3);
  transform: translateY(-3px);
}

.mode-card.active {
  border-color: rgba(184, 134, 11, 0.6);
  background: rgba(184, 134, 11, 0.08);
}

.mode-icon {
  font-size: 32px;
  font-weight: 700;
  color: #b8860b;
  margin-bottom: 12px;
}

.mode-card h3 {
  font-size: 18px;
  color: #e0e0e0;
  letter-spacing: 2px;
  margin-bottom: 8px;
}

.mode-card p {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}

.char-selector {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 32px;
}

.char-btn {
  width: 64px;
  height: 64px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(184, 134, 11, 0.15);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.char-btn:hover { border-color: rgba(184, 134, 11, 0.4); }
.char-btn.selected {
  border-color: #b8860b;
  background: rgba(184, 134, 11, 0.12);
}

.char-label { font-size: 22px; font-weight: 700; color: #e0e0e0; }
.char-pinyin { font-size: 11px; color: rgba(255, 255, 255, 0.4); margin-top: 2px; }

.duration-control {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 40px;
}

.duration-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
}

.duration-slider {
  display: flex;
  align-items: center;
  gap: 12px;
}

.duration-slider input[type="range"] {
  width: 160px;
  accent-color: #b8860b;
}

.duration-value {
  font-size: 14px;
  color: #b8860b;
  font-weight: 600;
  min-width: 40px;
}

.start-btn {
  display: block;
  margin: 0 auto;
  padding: 14px 48px;
  background: linear-gradient(135deg, #b8860b, #daa520);
  color: #1a1a2e;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 3px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(184, 134, 11, 0.3);
}

/* 指导阶段 */
.progress-bar {
  height: 3px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  margin-bottom: 8px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #b8860b, #daa520);
  transition: width 0.4s ease;
}

.progress-text {
  text-align: right;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
  margin-bottom: 32px;
}

.chenzi-display {
  text-align: center;
  margin-bottom: 32px;
}

.chenzi-char {
  font-size: 72px;
  font-weight: 700;
  background: linear-gradient(135deg, #b8860b, #daa520);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 4px;
}

.chenzi-pinyin {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 4px;
}

.chenzi-desc {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 8px;
  letter-spacing: 2px;
}

.chenzi-keywords {
  font-size: 13px;
  color: rgba(184, 134, 11, 0.5);
  margin-top: 6px;
  letter-spacing: 2px;
}

.practice-instruction {
  padding: 24px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(184, 134, 11, 0.12);
  border-radius: 10px;
  margin-bottom: 32px;
  text-align: center;
}

.instruction-area {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(184, 134, 11, 0.15);
  color: #daa520;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 12px;
}

.instruction-tip {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.7;
  letter-spacing: 1px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 24px;
}

.action-btn {
  padding: 10px 20px;
  border: 1px solid rgba(184, 134, 11, 0.25);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 1px;
}

.action-btn:hover:not(:disabled) {
  border-color: rgba(184, 134, 11, 0.5);
  color: #daa520;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.start-practice-btn {
  background: linear-gradient(135deg, #b8860b, #daa520);
  color: #1a1a2e;
  font-weight: 600;
  border: none;
}

.start-practice-btn:hover {
  box-shadow: 0 4px 16px rgba(184, 134, 11, 0.3);
}

.text-btn {
  display: block;
  margin: 0 auto;
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.35);
  font-size: 13px;
  cursor: pointer;
  letter-spacing: 1px;
  padding: 8px 16px;
  transition: color 0.3s ease;
}

.text-btn:hover { color: rgba(255, 255, 255, 0.6); }

/* 练习阶段 */
.practice-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  padding-top: 20px;
}

.timer-wrapper {
  position: relative;
  width: 240px;
  height: 240px;
}

.timer-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.timer-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.06);
  stroke-width: 6;
}

.timer-progress {
  fill: none;
  stroke: url(#timerGradient);
  stroke: #b8860b;
  stroke-width: 6;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.1s linear;
}

.timer-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.timer-char {
  font-size: 36px;
  font-weight: 700;
  color: rgba(184, 134, 11, 0.6);
  margin-bottom: 4px;
}

.timer-count {
  font-size: 48px;
  font-weight: 700;
  color: #e0e0e0;
}

.timer-hint {
  text-align: center;
  max-width: 400px;
}

.hint-area {
  display: inline-block;
  padding: 3px 10px;
  background: rgba(184, 134, 11, 0.12);
  color: #daa520;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 8px;
}

.hint-tip {
  display: block;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.6;
}

.skip-btn {
  margin-top: 16px;
}

/* 完成阶段 */
.done-stage {
  text-align: center;
  padding-top: 40px;
}

.done-icon {
  font-size: 64px;
  font-weight: 700;
  background: linear-gradient(135deg, #b8860b, #daa520);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
}

.done-title {
  font-size: 24px;
  color: #e0e0e0;
  letter-spacing: 3px;
  margin-bottom: 8px;
}

.done-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 2px;
  margin-bottom: 32px;
}

.done-stats {
  display: flex;
  gap: 48px;
  justify-content: center;
  margin-bottom: 40px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: #b8860b;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.done-stage .start-btn {
  margin-bottom: 16px;
}
</style>
