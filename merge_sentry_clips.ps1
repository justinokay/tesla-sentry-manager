param(
    [Parameter(Mandatory=$true)]
    [string]$inputPath,
    [Parameter(Mandatory=$true)]
    [string]$outputPath
)
try {
    ffmpeg -version
} catch {
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    Import-Module $env:ChocolateyInstall\helpers\chocolateyProfile.psm1
    refreshenv
    'ffmpeg' | % {choco upgrade $_ -y}
}
Write-Host "verify $inputPath" -BackgroundColor DarkGreen
if (!(Test-Path $inputPath)){echo "input path does not exist"exit 0}
Write-Host "verify $outputPath" -BackgroundColor DarkGreen
if (!(Test-Path $outputPath)){try {mkdir $outputPath -ea SilentlyContinue} catch{}}
$sentryFiles = (gci -r -filter "*-front.mp4" $inputPath | Sort-Object -Property Length).FullName
$totalCount = ($sentryFiles | measure).count
Write-Host "found $totalCount sentry footage files." -BackgroundColor DarkGreen

Write-Host "checking $outputPath for broken files" -BackgroundColor DarkGreen
$outputFiles = (gci -r $outputPath).FullName
$outputFilesCount = ($outputFiles | measure).count
Write-Host "$outputFilesCount already processed" -BackgroundColor DarkGreen

$outputFiles| % -parallel {
    try {
        ffmpeg -v error -sseof -10 -i $_ -f null NUL
        Write-Host "Good!: $_" -BackgroundColor DarkGreen
    }
    catch {
        Write-Host "Broken!: $_ " -BackgroundColor DarkRed
        ri $_ -wi -confirm:$false
    } 
}

Write-Host "processing totalCount sentry footage files." -BackgroundColor DarkGreen
$sentryFiles | % {
    Write-Host "Processing $currentCount\$totalCount" -BackgroundColor DarkGreen
    $front = $_
    $back = $_.replace('-front','-back')
    $left = $_.replace('-front','-left_repeater')
    $right = $_.replace('-front','-right_repeater')
    $outputFile = $_.replace('-front','').split('\') | select -Last 1
    $year = $outputFile.split('-')[0]
    $month= $outputFile.split('-')[1]
    $day = $outputFile.split('-')[2].split('_')[0]
    $hour = $outputFile.split('-')[2].split('_')[1]
    $minute = $outputFile.split('-')[3]
    $second = $outputFile.split('-')[4].Replace('.mp4','') 
    $creation_time = "${year}-${month}-${day} ${hour}:${minute}:${second}"
    Write-Host "file: $outputFile, $creation_time" -BackgroundColor DarkGreen
    if (!(Test-Path $front) -or !(Test-Path $back) -or !(Test-Path $left) -or !(Test-Path $right) ) {
        Write-Host "$outputFile is missing files, skipping..." -BackgroundColor DarkYellow
        $currentCount += 1
        return
    }
    else {
        ffmpeg -n -i $front -i $back -i $left -i $right `
            -c:v libx264 `
            -pix_fmt yuv420p `
            -filter_complex "[1:v]scale=1280x960[v1];[0:v][v1][2:v][3:v]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0[v]" `
            -metadata creation_time=$creation_time `
            -map "[v]" `
            "$outputPath\$outputFile"
        $currentCount += 1
    }
}
