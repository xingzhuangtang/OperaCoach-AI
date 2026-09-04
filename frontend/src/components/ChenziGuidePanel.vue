<script setup lang="ts">
import { ref, computed } from 'vue'
import { synthesizeSpeech, playAudio, stopAudio } from '../utils/tts'

const showPanel = ref(false)
const playingKey = ref<string | null>(null)

async function playChar(char: string) {
  const key = `char-${char}`
  if (playingKey.value === key) {
    stopAudio()
    playingKey.value = null
    return
  }
  try {
    playingKey.value = key
    const url = await synthesizeSpeech(char, 'longxiaochun')
    await playAudio(url)
  } catch {
    // ignore
  } finally {
    playingKey.value = null
  }
}

async function playTip(char: string, area: string, tip: string) {
  const key = `tip-${char}-${area}`
  if (playingKey.value === key) {
    stopAudio()
    playingKey.value = null
    return
  }
  try {
    playingKey.value = key
    const text = `${area}练习：${tip}`
    const url = await synthesizeSpeech(text, 'longxiaochun')
    await playAudio(url)
  } catch {
    // ignore
  } finally {
    playingKey.value = null
  }
}
const panelPosition = ref({ right: '20px', bottom: '20px' })
const isDragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })

const chenziGuide = [
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

const panelStyle = computed(() => ({
  right: panelPosition.value.right,
  bottom: panelPosition.value.bottom,
}))

const startDrag = (e: MouseEvent) => {
  isDragging.value = true
  dragOffset.value = { x: e.clientX, y: e.clientY }
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

const onDrag = (e: MouseEvent) => {
  if (!isDragging.value) return
  const dx = e.clientX - dragOffset.value.x
  const dy = e.clientY - dragOffset.value.y
  dragOffset.value = { x: e.clientX, y: e.clientY }
  const currentRight = parseInt(panelPosition.value.right) - dx
  const currentBottom = parseInt(panelPosition.value.bottom) - dy
  panelPosition.value = {
    right: Math.max(0, currentRight) + 'px',
    bottom: Math.max(0, currentBottom) + 'px',
  }
}

const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}
</script>

<template>
  <div class="chenzi-panel-wrapper" :style="panelStyle">
    <transition name="panel-fade">
      <div v-if="showPanel" class="chenzi-floating-panel">
        <div class="panel-header" @mousedown="startDrag">
          <span class="panel-title">衬字发声指南</span>
          <el-button size="small" text @click="showPanel = false">✕</el-button>
        </div>
        <div class="panel-body">
          <div v-for="item in chenziGuide" :key="item.char" class="guide-item">
            <div class="guide-char-row">
              <span class="guide-char">{{ item.char }}</span>
              <span class="guide-pinyin">({{ item.pinyin }})</span>
              <button
                class="play-btn"
                :class="{ playing: playingKey === `char-${item.char}` }"
                @click="playChar(item.char)"
                :title="`播放「${item.char}」发音`"
              >
                {{ playingKey === `char-${item.char}` ? '⏹' : '▶' }}
              </button>
            </div>
            <div class="guide-desc">{{ item.desc }}</div>
            <div class="guide-keywords">{{ item.keywords }}</div>
            <div v-if="item.practice" class="guide-practice">
              <div v-for="(p, pi) in item.practice" :key="pi" class="practice-tip">
                <span class="practice-area">{{ p.area }}</span>
                <span class="practice-text">{{ p.tip }}</span>
                <button
                  class="play-btn-sm"
                  :class="{ playing: playingKey === `tip-${item.char}-${p.area}` }"
                  @click="playTip(item.char, p.area, p.tip)"
                  title="朗读指导"
                >
                  {{ playingKey === `tip-${item.char}-${p.area}` ? '⏹' : '🔊' }}
                </button>
              </div>
            </div>
          </div>
          <div class="iron-rules">
            <div class="rules-title">三大铁律</div>
            <div class="rule-item">1. 早功不喝凉水，凉水锁喉</div>
            <div class="rule-item">2. 气大于声，感觉声带在挤就降调休息</div>
            <div class="rule-item">3. 清晨5-7点练功最佳，午后只吊不喊</div>
          </div>
        </div>
      </div>
    </transition>
    <el-button
      class="chenzi-panel-toggle"
      :type="showPanel ? 'warning' : 'primary'"
      circle
      @click="showPanel = !showPanel"
    >
      {{ showPanel ? '✕' : '参' }}
    </el-button>
  </div>
</template>

<style scoped>
.chenzi-panel-wrapper {
  position: fixed;
  z-index: 9999;
  right: 20px;
  bottom: 20px;
}

.chenzi-panel-toggle {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 48px;
  height: 48px;
  font-size: 16px;
  font-weight: 700;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.chenzi-floating-panel {
  position: absolute;
  right: 0;
  bottom: 60px;
  width: 320px;
  max-height: 500px;
  background: rgba(26, 26, 46, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(184, 134, 11, 0.2);
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(184, 134, 11, 0.1), rgba(58, 90, 120, 0.1));
  border-bottom: 1px solid rgba(184, 134, 11, 0.2);
  cursor: move;
  user-select: none;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #b8860b;
  letter-spacing: 2px;
}

.panel-body {
  padding: 12px;
  max-height: 420px;
  overflow-y: auto;
}

.guide-item {
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 6px;
  margin-bottom: 8px;
  border: 1px solid rgba(184, 134, 11, 0.08);
}

.guide-item:last-child {
  margin-bottom: 0;
}

.guide-char-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 4px;
}

.guide-char {
  font-size: 20px;
  font-weight: 700;
  color: #b8860b;
}

.guide-pinyin {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}

.guide-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 2px;
}

.guide-keywords {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.4;
}

.guide-practice {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed rgba(184, 134, 11, 0.2);
}

.practice-tip {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
  line-height: 1.5;
}

.practice-tip:last-child {
  margin-bottom: 0;
}

.practice-area {
  flex-shrink: 0;
  padding: 2px 6px;
  background: rgba(184, 134, 11, 0.15);
  color: #daa520;
  border-radius: 3px;
  font-weight: 500;
  font-size: 11px;
}

.practice-text {
  color: rgba(255, 255, 255, 0.65);
}

.iron-rules {
  margin-top: 12px;
  padding: 12px;
  background: rgba(184, 134, 11, 0.08);
  border: 1px solid rgba(184, 134, 11, 0.2);
  border-radius: 6px;
}

.rules-title {
  font-size: 13px;
  font-weight: 600;
  color: #b8860b;
  margin-bottom: 8px;
  letter-spacing: 1px;
}

.rule-item {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.6;
  margin-bottom: 4px;
}

.rule-item:last-child {
  margin-bottom: 0;
}

.play-btn {
  margin-left: auto;
  background: rgba(184, 134, 11, 0.2);
  border: 1px solid rgba(184, 134, 11, 0.3);
  color: #daa520;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.play-btn:hover {
  background: rgba(184, 134, 11, 0.35);
}

.play-btn.playing {
  background: rgba(184, 134, 11, 0.5);
  animation: pulse 1s infinite;
}

.play-btn-sm {
  flex-shrink: 0;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12px;
  padding: 2px 4px;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.play-btn-sm:hover {
  opacity: 1;
}

.play-btn-sm.playing {
  opacity: 1;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.panel-fade-enter-active,
.panel-fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.panel-fade-enter-from,
.panel-fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
