param([Parameter(Mandatory=$true)][string]$MetadataPath)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$m = Get-Content -LiteralPath $MetadataPath -Raw -Encoding UTF8 | ConvertFrom-Json
$root = [string]$m.root
$coverPath = Join-Path $root ([string]$m.cover)
$outPath = Join-Path $root ([string]$m.output)
$logoPath = Join-Path $root ([string]$m.logo)
$bmp = [System.Drawing.Bitmap]::new(1200,630)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode='AntiAlias'; $g.InterpolationMode='HighQualityBicubic'; $g.TextRenderingHint='AntiAliasGridFit'
function Brush($hex){ return [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml($hex)) }
function Font($size,$bold=$false){$style=[System.Drawing.FontStyle]::Regular;if($bold){$style=[System.Drawing.FontStyle]::Bold};return [System.Drawing.Font]::new('Arial',[single]$size,$style,[System.Drawing.GraphicsUnit]::Pixel)}
try {
  $g.Clear([System.Drawing.ColorTranslator]::FromHtml('#021222'))
  $navy=Brush '#021222'; $blue=Brush '#00AAFA'; $orange=Brush '#FC7C00';$white=Brush '#FFFFFF';$gray=Brush '#AFC9DF';$panel=Brush '#083655'
  $g.FillRectangle($blue,0,0,1200,12); $g.FillRectangle($orange,0,620,1200,10)
  $g.FillPolygon($panel,[System.Drawing.Point[]]@([System.Drawing.Point]::new(780,12),[System.Drawing.Point]::new(930,12),[System.Drawing.Point]::new(650,620),[System.Drawing.Point]::new(500,620)))
  $g.FillPolygon($panel,[System.Drawing.Point[]]@([System.Drawing.Point]::new(980,12),[System.Drawing.Point]::new(1055,12),[System.Drawing.Point]::new(800,620),[System.Drawing.Point]::new(725,620)))
  # Marca corporativa: utilizar logo aportado cuando este disponible, o texto de respaldo.
  if(Test-Path -LiteralPath $logoPath){
    $img=[System.Drawing.Image]::FromFile($logoPath)
    try {$w=[Math]::Min(310,[int](90*$img.Width/$img.Height));$g.DrawImage($img,55,35,$w,90)}finally{$img.Dispose()}
  } else {
    $g.DrawString('IN',$(Font 80 $true), $blue,55,32)
    $g.DrawString('CORE',$(Font 80 $true),$orange,145,32)
    $g.DrawString('Knowledge Studio',$(Font 30),$gray,58,112)
  }
  $g.DrawString('BOLETIN TECNICO INTERACTIVO',$(Font 25 $true),$gray,55,176)
  $title=([string]$m.title).Trim(); if(!$title){throw 'Titulo social vacio'}
  $words=$title -split '\s+';
  # Particion equilibrada: maximo dos lineas y ajuste de fuente.
  $lines=@($title); if($words.Count -ge 2){
    $best=[double]::PositiveInfinity; $split=1
    for($i=1;$i -lt $words.Count;$i++){
      $a=($words[0..($i-1)] -join ' ');$b=($words[$i..($words.Count-1)] -join ' ')
      $d=[Math]::Abs($a.Length-$b.Length);if($d -lt $best){$best=$d;$split=$i}
    }
    $lines=@(($words[0..($split-1)] -join ' '),($words[$split..($words.Count-1)] -join ' '))
  }
  $fontSize=51; $maxW=495
  do {
    if($fontSize -lt 25){throw 'El titulo es demasiado largo para dos lineas legibles. Acortelo en config.js (social.titulo).'}
    $f=Font $fontSize $true
    $ok=$true;foreach($line in $lines){if($g.MeasureString($line,$f).Width -gt $maxW){$ok=$false}}
    if(!$ok){$f.Dispose();$fontSize-=2}
  }while(!$ok)
  try {for($j=0;$j -lt $lines.Count;$j++){$b=$white;if($j -eq 1){$b=$orange};$g.DrawString($lines[$j],$f,$b,55,(240+$j*70))}} finally{$f.Dispose()}
  $g.FillRectangle($blue,55,412,490,84)
  $g.DrawString('ABRIR BOLETIN  ->',$(Font 32 $true),$navy,76,433)
  # Autoria dinamica: se muestra bajo ABRIR BOLETIN, solo cuando config.js autor tiene texto.
  $author=([string]$m.author).Trim()
  if($author){
    $authorSize=21; $maxAuthorW=695
    do {
      if($authorSize -lt 13){throw 'Autor demasiado largo para portada social. Acortelo en config.js (autor).'}
      $authorFont=Font $authorSize
      $fits=$g.MeasureString($author,$authorFont).Width -le $maxAuthorW
      if(-not $fits){$authorFont.Dispose();$authorSize-=1}
    }while(-not $fits)
    try {$g.DrawString($author,$authorFont,$gray,55,536)}finally{$authorFont.Dispose()}
  }
  if(!(Test-Path -LiteralPath $coverPath)){throw ('No existe la primera lamina: '+$coverPath)}
  $page=[System.Drawing.Image]::FromFile($coverPath)
  try {
    $x=795;$y=35;$boxW=345;$boxH=520
    $g.FillRectangle($white,$x-10,$y-10,$boxW+20,$boxH+20)
    $ratio=[Math]::Min($boxW/$page.Width,$boxH/$page.Height)
    $dw=[int]($page.Width*$ratio);$dh=[int]($page.Height*$ratio)
    $dx=$x+[int](($boxW-$dw)/2);$dy=$y+[int](($boxH-$dh)/2)
    $g.DrawImage($page,$dx,$dy,$dw,$dh)
  } finally {$page.Dispose()}
  $jpg=[System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object {$_.MimeType -eq 'image/jpeg'} | Select-Object -First 1
  $encoder=[System.Drawing.Imaging.EncoderParameters]::new(1)
  $encoder.Param[0]=[System.Drawing.Imaging.EncoderParameter]::new([System.Drawing.Imaging.Encoder]::Quality,[long]91)
  $outDir=Split-Path -Parent $outPath;New-Item -ItemType Directory -Force -Path $outDir | Out-Null
  $bmp.Save($outPath,$jpg,$encoder)
  $encoder.Dispose()
  Write-Output ('PASS: Portada social generada: '+$outPath)
}finally{$g.Dispose();$bmp.Dispose()}
