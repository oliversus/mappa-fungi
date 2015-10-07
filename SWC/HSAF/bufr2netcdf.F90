PROGRAM BUFR2NETCDF
  !
  !  PURPOSE: DECODE THE OPERATIONAL 1 KM - SOIL MOISTURE PRODUCT IN BUFR FORMAT,
  !           RE-ENCODE IN netCDF FORMAT
  !  EXTERNALS: BUFREX, BUSEL2, BUS0123, PBBUFR, PBOPEN, PBCLOSE
  !  COMPILATION: sudo gfortran -Wl,-rpath -Wl,/usr/local/lib -o bufr2netcdf bufr2netcdf.F90 -L${NETCDF_libdir} -lnetcdf -lnetcdff -I${NETCDF_incdir} -L${HDF_libdir} -lhdf5_hl -lhdf5 -L${BUFR_libdir} -lbufr; with *_libdir=/usr/local/lib and  export LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH}
  !  CALL: bufr2netcdf <BUFR file's name>
  !  OUTPUT: NetCDF file, with extension (i.e. everything after the last dot) replaced by 'nc'
  !          (h08_20090816_105100_metopa_14658_ZAMG.buf becomes h08_20090816_105100_metopa_14658_ZAMG.nc)
  !  AUTHOR: Alexander Jann / ZAMG
  !  DATE: 04/11/09 (+ bug fix in 08/11)
  !
  USE netcdf
  IMPLICIT NONE
  INTEGER :: I, INDEX1D, INDEX2D, ERR, SUBSET_NR, JUMP, JUMP_SM, N, NLAT, NLON, NR_PIXELS, UNIT
  !  BUFR
  INTEGER, PARAMETER ::  JSUP=9,  JSEC0=3,      JSEC1=40,     JSEC2=4096  , JSEC3=4,  &
       JSEC4=2, JELEM=160000, JBUFL=512000, KELEM=160000, KVALS=4096000, JBYTE=440000
  INTEGER :: KSUP(JSUP), KSEC0(JSEC0), KSEC1(JSEC1)
  INTEGER :: KSEC2(JSEC2), KSEC3(JSEC3), KSEC4(JSEC4)
  INTEGER :: KBUFL, KDLEN, KEL, KTDLEN, KTDEXL
  INTEGER, DIMENSION(JBUFL) :: KBUFF
  REAL*8,  DIMENSION(KVALS) :: VALUES
  INTEGER, DIMENSION(JELEM) :: KTDLST, KTDEXP
  CHARACTER (LEN=64), DIMENSION(KELEM) :: CNAMES
  CHARACTER (LEN=24), DIMENSION(KELEM) :: CUNITS
  CHARACTER (LEN=80), DIMENSION(KELEM) :: CVALS

  ! IDs for the netCDF file, dimensions, and variables...
  INTEGER   :: NCID, LON_DIMID, LAT_DIMID, DIMIDS(2)
  INTEGER   :: LAT_VARID, LON_VARID
  INTEGER   :: SOMO_VARID, SOMO_ERR_VARID, SOMO_FLAG5_VARID, SOMO_FLAG6_VARID

  !  ...ranges...
  REAL      :: SOMO_RANGE(2) = (/0., 100./)
  INTEGER*2 :: FLAG_RANGE(2) = (/0, 255/)

  !  ...names.
  CHARACTER (LEN = *), PARAMETER :: LAT_NAME = "latitude", LON_NAME = "longitude"
  CHARACTER (LEN = *), PARAMETER :: UNITS = "units", SOMO_UNITS = "%"

  CHARACTER (LEN = *), PARAMETER :: LAT_UNITS = "degrees_north", LON_UNITS = "degrees_east"

  !  SM data
  REAL, DIMENSION(:), ALLOCATABLE    ::  SOMO, SOMO_ERR, LAMBDA, PHI
  INTEGER*2, DIMENSION(:), ALLOCATABLE  ::  FLAG_40005, FLAG_40006
  CHARACTER (LEN=255) :: IFILNAM, OFILNAM

  INTEGER :: debug=0

  DATA KSEC0,KSEC2,KSEC3,KSEC4,KTDLST &
       /JSEC0*0,JSEC2*0,JSEC3*0,JSEC4*0,JELEM*0/

  !  1. Open BUFR file
  !  -------------------------------------

  CALL GETARG(1,IFILNAM)
  ERR=0
  CALL PBOPEN(UNIT,IFILNAM,'R',ERR)
  IF ( ERR == -1 ) STOP 'OPEN FAILED'
  IF ( ERR == -2 ) STOP 'INVALID FILE NAME'
  IF ( ERR == -3 ) STOP 'INVALID OPEN MODE SPECIFIED'

  !  2. Decode prologue
  !  -------------------------------------

  ERR=0
  CALL PBBUFR(UNIT,KBUFF,JBYTE*4,KBUFL,ERR)
  IF (ERR /= 0) STOP 'cannot even read the prologue :-('
  KBUFL=KBUFL/4+1
  CALL BUS0123(KBUFL, KBUFF, KSUP, KSEC0, KSEC1, KSEC2, KSEC3, ERR)
  KEL=KVALS/KSEC3(3)
  IF (KEL > KELEM) KEL=KELEM

  !  Expand BUFR message.
  CALL BUFREX(KBUFL, KBUFF, KSUP, KSEC0, KSEC1, KSEC2, KSEC3, KSEC4, &
       KEL, CNAMES, CUNITS, KVALS, VALUES, CVALS, ERR)
  NLON=NINT((VALUES(4)-VALUES(3))/0.00416667) ! maximum; # of columns may actually be less 
  NLAT=NINT((VALUES(6)-VALUES(5))/0.00416667)
  NR_PIXELS=NLON*NLAT
  ALLOCATE(SOMO(1:NR_PIXELS))
  ALLOCATE(SOMO_ERR(1:NR_PIXELS))
  ALLOCATE(FLAG_40005(1:NR_PIXELS))
  ALLOCATE(FLAG_40006(1:NR_PIXELS))
  ALLOCATE(LAMBDA(1:NLON))
  ALLOCATE(PHI(1:NLAT))

  !  3.  Decode actual soil moisture data.
  !  -------------------------------------

  INDEX1D=1
  INDEX2D=1

  MSSLOOP: DO
     KBUFL=0
     CALL PBBUFR(UNIT,KBUFF,JBYTE*4,KBUFL,ERR)
     IF (ERR == -1) THEN
        CALL PBCLOSE(UNIT,ERR)
        EXIT MSSLOOP
     ENDIF

     IF (ERR == -2) STOP 'FILE HANDLING PROBLEM' 
     IF (ERR == -3) STOP 'ARRAY TOO SMALL FOR PRODUCT'
     N=N+1
     KBUFL=KBUFL/4+1
     CALL BUS0123(KBUFL, KBUFF, KSUP, KSEC0, KSEC1, KSEC2, KSEC3, ERR)

     IF (ERR /= 0) THEN
        PRINT*,'ERROR IN BUS0123: ',ERR, 'FOR MESSAGE NUMBER ',N
        ERR=0
        CYCLE MSSLOOP
     ENDIF
     KEL=KVALS/KSEC3(3)
     IF (KEL > KELEM) KEL=KELEM
     !  Expand BUFR message.
     CALL BUFREX(KBUFL, KBUFF, KSUP, KSEC0, KSEC1, KSEC2, KSEC3, KSEC4, &
          KEL, CNAMES, CUNITS, KVALS, VALUES, CVALS, ERR)

     IF (ERR /= 0) CALL EXIT(2)
     ISSLOOP:  DO SUBSET_NR=0,KSUP(6)-1
        JUMP=SUBSET_NR*KEL
        CALL BUSEL2(SUBSET_NR+1,KEL,KTDLEN,KTDLST,KTDEXL,KTDEXP,CNAMES, &
             CUNITS,ERR)
        LAMBDA(INDEX1D)=VALUES(JUMP+1)
        IF (INDEX1D == 1) THEN 
           DO I=1,NLAT
              PHI(I)=VALUES(JUMP+2)+0.00416667*(I-1)
           END DO
        ENDIF
        INDEX1D=INDEX1D+1
        !   Resolve replication
        JUMP_SM=JUMP+5
        DO I=1,VALUES(JUMP+4)
           SOMO(INDEX2D)=VALUES(JUMP_SM)
           SOMO_ERR(INDEX2D)=VALUES(JUMP_SM+1)
           FLAG_40005(INDEX2D)=VALUES(JUMP_SM+2)
           IF (VALUES(JUMP_SM+3) > 65535.) THEN 
              FLAG_40006(INDEX2D)=255
           ELSE
              FLAG_40006(INDEX2D)=VALUES(JUMP_SM+3)
           ENDIF
           JUMP_SM=JUMP_SM+4
           INDEX2D=INDEX2D+1
        END DO
     END DO ISSLOOP
  END DO MSSLOOP
  !   4. Create the netCDF file and variables.
  !  ----------------------------------------
  OFILNAM=IFILNAM(1:SCAN(IFILNAM,'.',.TRUE.))//'nc'
  CALL CHECK( NF90_CREATE(OFILNAM, NF90_HDF5, NCID) )

  ! Define the dimensions.

  NLON=INDEX1D-1
  CALL CHECK( NF90_DEF_DIM(NCID, LAT_NAME, NLAT, LAT_DIMID) )
  CALL CHECK( NF90_DEF_DIM(NCID, LON_NAME, NLON, LON_DIMID) )
  ! Define the coordinate variables. They will hold the coordinate
  ! information, that is, the latitudes and longitudes. A varid is
  ! returned for each.
  CALL CHECK( NF90_DEF_VAR(NCID, LAT_NAME, NF90_FLOAT, LAT_DIMID, LAT_VARID) )
  CALL CHECK( NF90_DEF_VAR(NCID, LON_NAME, NF90_FLOAT, LON_DIMID, LON_VARID) )
  ! Assign units attributes to coordinate var data. This attaches a
  ! text attribute to each of the coordinate variables, containing the
  ! units.
  CALL CHECK( NF90_PUT_ATT(NCID, LAT_VARID, UNITS, LAT_UNITS) )
  CALL CHECK( NF90_PUT_ATT(NCID, LON_VARID, UNITS, LON_UNITS) )
  ! The dimids array is used to pass the dimids of the dimensions of
  !      the netCDF variables. All netCDF variables we are
  !      creating share the same two dimensions.
  DIMIDS = (/ LON_DIMID, LAT_DIMID /)
  ! Define the netCDF variables for the soil moisture data.
  CALL CHECK( NF90_DEF_VAR(NCID, "soil_moisture", NF90_FLOAT, DIMIDS, SOMO_VARID) )
  CALL CHECK( NF90_PUT_ATT(NCID, SOMO_VARID, UNITS, SOMO_UNITS) )

  CALL CHECK( NF90_PUT_ATT(NCID, SOMO_VARID, "valid_range", SOMO_RANGE) )
  CALL CHECK( NF90_DEF_VAR_DEFLATE(NCID, SOMO_VARID, 1, 1, 9) )
  CALL CHECK( NF90_DEF_VAR(NCID, "soil_moisture_error", NF90_FLOAT, DIMIDS, SOMO_ERR_VARID) )
  CALL CHECK( NF90_PUT_ATT(NCID, SOMO_ERR_VARID, UNITS, SOMO_UNITS) )
  CALL CHECK( NF90_PUT_ATT(NCID, SOMO_ERR_VARID, "valid_range", SOMO_RANGE) )
  CALL CHECK( NF90_DEF_VAR_DEFLATE(NCID, SOMO_ERR_VARID, 1, 1, 9) )
  CALL CHECK( NF90_DEF_VAR(NCID, "soil_moisture_correction_flag", NF90_SHORT, DIMIDS, SOMO_FLAG5_VARID) )
  CALL CHECK( NF90_PUT_ATT(NCID, SOMO_FLAG5_VARID, "valid_range", FLAG_RANGE) )
  CALL CHECK( NF90_DEF_VAR_DEFLATE(NCID, SOMO_FLAG5_VARID, 1, 1, 9) )
  CALL CHECK( NF90_DEF_VAR(NCID, "soil_moisture_processing_flag", NF90_SHORT, DIMIDS, SOMO_FLAG6_VARID) )
  CALL CHECK( NF90_PUT_ATT(NCID, SOMO_FLAG6_VARID, "valid_range", FLAG_RANGE) )
  CALL CHECK( NF90_DEF_VAR_DEFLATE(NCID, SOMO_FLAG6_VARID, 1, 1, 9) )
  ! End define mode.
  CALL CHECK( NF90_ENDDEF(NCID) )
  !   5. Write the netCDF file, clean up and leave.
  !  ---------------------------------------------
  ! Write the coordinate variable data. This will put the latitudes
  ! and longitudes of our data grid into the netCDF file.
  CALL CHECK( NF90_PUT_VAR(NCID, LAT_VARID, PHI) )
  CALL CHECK( NF90_PUT_VAR(NCID, LON_VARID, LAMBDA(1:NLON)) )
  ! Write the soil moisture data to the netCDF file
  CALL CHECK( NF90_PUT_VAR(NCID, SOMO_VARID, TRANSPOSE(RESHAPE(SOMO(1:INDEX2D-1),(/NLAT, NLON/)))) )
  CALL CHECK( NF90_PUT_VAR(NCID, SOMO_ERR_VARID, TRANSPOSE(RESHAPE(SOMO_ERR(1:INDEX2D-1),(/NLAT, NLON/)))) )
  CALL CHECK( NF90_PUT_VAR(NCID, SOMO_FLAG5_VARID, TRANSPOSE(RESHAPE(FLAG_40005(1:INDEX2D-1),(/NLAT, NLON/)))) )
  CALL CHECK( NF90_PUT_VAR(NCID, SOMO_FLAG6_VARID, TRANSPOSE(RESHAPE(FLAG_40006 (1:INDEX2D-1),(/NLAT, NLON/)))) )
  ! Close the file.
  CALL CHECK( NF90_CLOSE(NCID) )
  DEALLOCATE(SOMO_ERR)
  DEALLOCATE(SOMO)
  DEALLOCATE(FLAG_40005)
  DEALLOCATE(FLAG_40006)
  DEALLOCATE(LAMBDA)
  DEALLOCATE(PHI)
  WRITE(*,*) "*** SUCCESS in writing ",OFILNAM

CONTAINS

  SUBROUTINE CHECK(STATUS)
    INTEGER, INTENT ( IN) :: STATUS
    IF (STATUS /= NF90_NOERR) THEN 
       WRITE(*,*) NF90_STRERROR(STATUS)
       STOP 2
    END IF
  END SUBROUTINE CHECK

END PROGRAM BUFR2NETCDF
