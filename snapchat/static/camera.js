
const video = document.getElementById('video')
const canvas = document.getElementById('canvas')
const preview = document.getElementById('preview')
const overlay = document.getElementById('overlay')
const capture = document.getElementById('capture')
const retake = document.getElementById('retake')
const send = document.getElementById('send')
const sendLabel = document.getElementById('sendLabel')
const sendPanel = document.getElementById('sendPanel')
const directSendDock = document.getElementById('directSendDock')
const statusBox = document.getElementById('status')
const caption = document.getElementById('caption')
const captionWrap = document.getElementById('captionWrap')
const selectAll = document.getElementById('select-all')
const selectedCount = document.getElementById('selectedCount')
const selectedChips = document.getElementById('selectedChips')
const filterStrip = document.getElementById('filterStrip')
const captureDock = document.getElementById('captureDock')
const receiverCheckboxes = Array.from(document.querySelectorAll('.receiver-checkbox'))


const openDiskBtn = document.getElementById('open-disk-btn')
const imageInput = document.getElementById('image-input')
const imagePreview = document.getElementById('image-preview')
const imagePath = document.getElementById('image-path')


// const isDirectSnap = {% if is_direct_snap %}true{% else %} false{% endif %}


openDiskBtn.addEventListener('click', () => {
    imageInput.click()
})

imageInput.addEventListener('change', () => {
    const file = imageInput.files[0]
    if (file) {
        previewImage(file)
        imageContainer.classList.remove('hidden')
        imageContainer.classList.add('flex')
    }
})

function previewImage(file) {
    imagePath.textContent = file.name
    imagePreview.src = URL.createObjectURL(file)
}




let currentFilter = 'none'
let currentEffect = 'none'
let capturedBlob = null

function getCSRFToken() {
    const inputToken = document.querySelector('[name=csrfmiddlewaretoken]')
    const metaToken = document.querySelector('meta[name="csrf-token"]')
    return (inputToken && inputToken.value) || (metaToken && metaToken.content) || ''
}

function showStatus(message, isError = false) {
    statusBox.textContent = message
    statusBox.classList.remove('hidden', 'bg-red-500', 'bg-[#fffc00]', 'text-black', 'text-white')
    statusBox.classList.add(isError ? 'bg-red-500' : 'bg-[#fffc00]', isError ? 'text-white' : 'text-black')
    window.clearTimeout(showStatus.timer)
    showStatus.timer = window.setTimeout(() => {
        statusBox.classList.add('hidden')
    }, 2600)
}

function clearStatus() {
    statusBox.classList.add('hidden')
    statusBox.textContent = ''
}

async function openWebCam() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showStatus('Camera is not available in this browser.', true)
        return
    }

    try {
        video.srcObject = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user' },
            audio: false
        })
    } catch (error) {
        showStatus('Allow camera permission to take a snap.', true)
    }
}

function drawSpark(context, width, height) {
    context.fillStyle = 'rgba(255, 252, 0, .78)'
    for (let index = 0; index < 18; index += 1) {
        const x = (width * ((index * 37) % 100)) / 100
        const y = (height * ((index * 23) % 75)) / 100
        const size = Math.max(5, width * (index % 3 === 0 ? .018 : .011))
        context.beginPath()
        context.arc(x, y, size, 0, Math.PI * 2)
        context.fill()
    }
}

function drawFrame(context, width, height) {
    const inset = Math.max(16, width * .045)
    context.strokeStyle = 'rgba(255, 252, 0, .9)'
    context.lineWidth = Math.max(5, width * .014)
    context.lineCap = 'round'
    context.strokeRect(inset, inset, width - inset * 2, height - inset * 2)
}

function drawHeartShape(context, x, y, size) {
    context.save()
    context.translate(x, y)
    context.scale(size, size)
    context.beginPath()
    context.moveTo(0, .32)
    context.bezierCurveTo(-.72, -.18, -.42, -.78, 0, -.42)
    context.bezierCurveTo(.42, -.78, .72, -.18, 0, .32)
    context.closePath()
    context.fillStyle = 'rgba(255, 45, 85, .92)'
    context.fill()
    context.restore()
}

function drawHearts(context, width, height) {
    const size = Math.max(38, width * .115)
    drawHeartShape(context, width * .22, height * .18, size)
    drawHeartShape(context, width * .78, height * .2, size * .92)
    drawHeartShape(context, width * .5, height * .12, size * .76)
}

function drawDog(context, width, height) {
    const centerX = width * .5
    const topY = height * .16
    const earSize = Math.max(42, width * .14)
    const noseSize = Math.max(14, width * .035)

    context.fillStyle = 'rgba(91, 55, 34, .92)'
    context.beginPath()
    context.ellipse(centerX - earSize * 1.05, topY, earSize * .42, earSize * .78, -.45, 0, Math.PI * 2)
    context.fill()

    context.beginPath()
    context.ellipse(centerX + earSize * 1.05, topY, earSize * .42, earSize * .78, .45, 0, Math.PI * 2)
    context.fill()

    context.fillStyle = 'rgba(40, 24, 16, .95)'
    context.beginPath()
    context.ellipse(centerX, topY + earSize * .85, noseSize * 1.25, noseSize, 0, 0, Math.PI * 2)
    context.fill()

    context.strokeStyle = 'rgba(40, 24, 16, .85)'
    context.lineWidth = Math.max(3, width * .008)
    context.lineCap = 'round'
    context.beginPath()
    context.moveTo(centerX, topY + earSize * 1.05)
    context.quadraticCurveTo(centerX - noseSize, topY + earSize * 1.25, centerX - noseSize * 1.8, topY + earSize * 1.15)
    context.moveTo(centerX, topY + earSize * 1.05)
    context.quadraticCurveTo(centerX + noseSize, topY + earSize * 1.25, centerX + noseSize * 1.8, topY + earSize * 1.15)
    context.stroke()
}

function drawEffect(context, width, height) {
    if (currentEffect === 'heart') {
        drawHearts(context, width, height)
    }

    if (currentEffect === 'dog') {
        drawDog(context, width, height)
    }

    if (currentEffect === 'spark') {
        drawSpark(context, width, height)
    }

    if (currentEffect === 'frame') {
        drawFrame(context, width, height)
    }
}

function setOverlay() {
    overlay.innerHTML = ''
    overlay.classList.add('hidden')

    if (currentEffect === 'spark') {
        overlay.classList.remove('hidden')
        overlay.innerHTML = '<div class="absolute left-[14%] top-[18%] h-4 w-4 rounded-full bg-[#fffc00]/80"></div><div class="absolute right-[16%] top-[23%] h-6 w-6 rounded-full bg-[#fffc00]/75"></div><div class="absolute left-[48%] top-[12%] h-3 w-3 rounded-full bg-[#fffc00]/90"></div><div class="absolute bottom-[34%] right-[20%] h-4 w-4 rounded-full bg-[#fffc00]/70"></div>'
    }

    if (currentEffect === 'heart') {
        overlay.classList.remove('hidden')
        overlay.innerHTML = '<i class="fa-solid fa-heart absolute left-[18%] top-[14%] text-5xl text-pink-500 drop-shadow-lg"></i><i class="fa-solid fa-heart absolute right-[18%] top-[16%] text-5xl text-pink-500 drop-shadow-lg"></i><i class="fa-solid fa-heart absolute left-1/2 top-[9%] -translate-x-1/2 text-4xl text-pink-500 drop-shadow-lg"></i>'
    }

    if (currentEffect === 'dog') {
        overlay.classList.remove('hidden')
        overlay.innerHTML = '<div class="absolute left-1/2 top-[10%] h-20 w-52 -translate-x-1/2"><div class="absolute left-2 top-0 h-20 w-12 -rotate-[24deg] rounded-full bg-[#5b3722]/90"></div><div class="absolute right-2 top-0 h-20 w-12 rotate-[24deg] rounded-full bg-[#5b3722]/90"></div><div class="absolute left-1/2 top-16 h-5 w-7 -translate-x-1/2 rounded-full bg-[#281810]"></div></div>'
    }

    if (currentEffect === 'frame') {
        overlay.classList.remove('hidden')
        overlay.innerHTML = '<div class="absolute inset-5 rounded-[32px] border-4 border-[#fffc00]/90"></div>'
    }
}

function updateSelectedFriends() {
    const selected = receiverCheckboxes.filter((checkbox) => checkbox.checked)

    if (isDirectSnap) {
        return
    }

    receiverCheckboxes.forEach((checkbox) => {
        const option = checkbox.closest('.friend-option')
        option.classList.toggle('is-selected', checkbox.checked)
        const subtitle = option.querySelector('.friend-subtitle')
        subtitle.textContent = checkbox.checked ? 'Added to snap' : 'Tap to add recipient'
    })

    selectedCount.textContent = selected.length
        ? `${selected.length} friend${selected.length === 1 ? '' : 's'} selected`
        : 'Choose friends for this snap'

    selectAll.textContent = selected.length === receiverCheckboxes.length && receiverCheckboxes.length
        ? 'Clear'
        : 'Select all'

    selectedChips.innerHTML = ''
    selected.forEach((checkbox) => {
        const name = checkbox.closest('.friend-option').dataset.friendName
        const chip = document.createElement('span')
        chip.className = 'selected-chip flex flex-shrink-0 items-center gap-2 rounded-full bg-black px-3 py-2 text-xs font-extrabold text-[#fffc00]'
        const icon = document.createElement('i')
        icon.className = 'fa-solid fa-user'
        const label = document.createElement('span')
        label.textContent = name
        chip.append(icon, label)
        selectedChips.appendChild(chip)
    })
}

document.querySelectorAll('.filter').forEach((button) => {
    button.addEventListener('click', () => {
        currentFilter = button.dataset.filter
        currentEffect = button.dataset.effect

        video.style.filter = currentFilter
        preview.style.filter = currentFilter
        setOverlay()

        document.querySelectorAll('.filter').forEach((filterButton) => {
            filterButton.classList.remove('is-active')
        })
        button.classList.add('is-active')
    })
})

receiverCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener('change', updateSelectedFriends)
})

capture.addEventListener('click', () => {
    clearStatus()

    if (!video.videoWidth || !video.videoHeight) {
        showStatus('Camera is still loading.', true)
        return
    }

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const context = canvas.getContext('2d')
    context.filter = currentFilter
    context.drawImage(video, 0, 0, canvas.width, canvas.height)
    context.filter = 'none'
    drawEffect(context, canvas.width, canvas.height)

    canvas.toBlob((blob) => {
        capturedBlob = blob
        preview.src = URL.createObjectURL(blob)
        preview.classList.remove('hidden')
        video.classList.add('hidden')
        captureDock.classList.add('hidden')
        filterStrip.classList.add('hidden')
        retake.classList.remove('hidden')
        retake.classList.add('flex')
        captionWrap.classList.remove('hidden')
        if (isDirectSnap) {
            directSendDock.classList.remove('hidden')
        } else {
            sendPanel.classList.add('is-open')
        }
        updateSelectedFriends()
    }, 'image/png')
})

retake.addEventListener('click', () => {
    clearStatus()
    capturedBlob = null
    preview.src = ''
    preview.classList.add('hidden')
    video.classList.remove('hidden')
    captureDock.classList.remove('hidden')
    filterStrip.classList.remove('hidden')
    retake.classList.add('hidden')
    retake.classList.remove('flex')
    captionWrap.classList.add('hidden')
    if (isDirectSnap) {
        directSendDock.classList.add('hidden')
    } else {
        sendPanel.classList.remove('is-open')
    }
    send.disabled = false
    sendLabel.textContent = isDirectSnap ? 'Send to {{ direct_friend.username|default:"friend" }}' : 'Send Snap'
})

if (selectAll) {
    selectAll.addEventListener('click', () => {
        const shouldSelect = receiverCheckboxes.some((checkbox) => !checkbox.checked)
        receiverCheckboxes.forEach((checkbox) => {
            checkbox.checked = shouldSelect
        })
        updateSelectedFriends()
    })
}

send.addEventListener('click', async () => {
    clearStatus()

    if (!capturedBlob) {
        showStatus('Take a snap first.', true)
        return
    }

    const selectedReceivers = receiverCheckboxes.filter((checkbox) => checkbox.checked)
    if (selectedReceivers.length === 0) {
        showStatus('Choose at least one friend.', true)
        return
    }

    const formData = new FormData()
    formData.append('image', new File([capturedBlob], 'snap.png', { type: 'image/png' }))
    formData.append('caption', caption.value.trim())
    selectedReceivers.forEach((checkbox) => {
        formData.append('receivers', checkbox.value)
    })

    send.disabled = true
    sendLabel.textContent = 'Sending...'

    try {
        const response = await fetch('{% url "send-snap" %}', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        })

        const data = await response.json()

        if (!response.ok) {
            throw new Error(data.error || 'Snap could not be sent.')
        }

        showStatus(`Sent to ${data.receiver_count} friend${data.receiver_count === 1 ? '' : 's'}.`)
        sendLabel.textContent = 'Sent'
        window.setTimeout(() => {
            retake.click()
            caption.value = ''
        }, 650)
    } catch (error) {
        showStatus(error.message, true)
        send.disabled = false
        sendLabel.textContent = 'Send Snap'
    }
})

updateSelectedFriends()
openWebCam()
