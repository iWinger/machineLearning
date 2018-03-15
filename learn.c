#include <stdio.h>
#include <stdlib.h>
#include <string.h>

double** transpose(double *input[], int row, int col){
/* switch the columns with the rows n x m becomes m x n*/
int tRow = col;
int tCol = row;
int i = 0 ;
int t1 = 0;
int t2 = 0;
double** tranMatrix = (double**)malloc(tRow * sizeof(double*));
	for( i = 0; i < tRow; i++){
		tranMatrix[i] = malloc(tCol* sizeof(double));	
	}
	/* use tcol as original row and trow as original col */
	for( t1 = 0; t1 < tCol; t1++){
		for( t2 = 0; t2 < tRow; t2++){
			tranMatrix[t2][t1] = input[t1][t2];
		}
	}
return tranMatrix;
}

double** identity(double *input[], int col){
/* identity matrix should be square */
int identityR = col;
int identityC = identityR;
int i = 0;
int x = 0;
int y = 0;
double** idMatrix = (double**)malloc(identityR * sizeof(double*));
        for(i = 0; i < identityR; i++){
                idMatrix[i] = malloc(identityC * sizeof(double));
	}
	/* fill the diagonals with ones */
	while(x < identityR){
	idMatrix[x][y] = 1.000000;
	x++;
	y++;	
	}

return idMatrix;

}

double** multiply(double *input[], double *dupinput[], int rowOne, int colOne, int rowTwo, int colTwo){
double sum = 0;
int arr1row = rowOne;
int arr1col = colOne;
int arr2row = rowTwo;
int arr2col = colTwo;
int a = 0;
int b = 0;
int c = 0;
int m = 0;
double** newMatrix = (double**)malloc(arr1row * sizeof(double*));
	for( m = 0; m < arr1row; m++){
		newMatrix[m] = malloc(arr2col * sizeof(double));
	}


/* IF the num of column of first matrix doesn't equal the num of row of the sec */
if(arr1col != arr2row)
exit(0);
/* have a sum for each sum of multiplied element from each row in array1 and each column in array2 */
	for(a = 0; a < arr1row; a++){
		for(b = 0; b < arr2col; b++){
			for(c = 0; c < arr1col; c++){
				sum = (sum + (input[a][c] * dupinput[c][b]));
				
			}
			newMatrix[a][b] = sum;
			sum = 0;
		}
	}
	
return newMatrix;
}

void printIt(double *arr[], int row, int col){
/* print out all of the contents of the array */
int x = 0;
int y = 0;
	for( x = 0; x < row; x++){
		for( y = 0; y < col; y++){
		printf("%lf ", arr[x][y]);
		}
	printf("\n");
	}	

}

void printPrice(double *arr[], int row, int col){
/* same as the printIt function, but just round the double to an integer */
int x = 0;
int y = 0;
	for( x = 0; x < row; x++){
		for( y = 0; y < col; y++){
		printf("%.0f\n", arr[x][y]);
		}

	}
}
double** invert(double *input[], int len){
   int a = 0;
   int b = 0;
   int m = 0;
   int n = 0;
   /* since an invertible matrix is a square matrix, it should have the same number of rows as columns*/
   int sqLength = len;
   int a2 = sqLength-1;
   int c1 = sqLength-1;
   int c2 = sqLength-1;
   double** idMatrix = identity(input, sqLength);
   
   /* make entire row have respective 1 with operations  */
	 while(m < (sqLength)){
		/* store number below pivot */
		double pivotstore = input[m][n];
		
	      for( a = 0; a < sqLength; a++){
	        /* only make sure pivot gets reduced to sqLength amount of times */
		/* scaling pivot number to 1 in rref */
		/* make sure diagonals have 1's */
		/* need a store for [m][n] */
				
				/* scaling */	
				idMatrix[m][a] = idMatrix[m][a] * (1.000000 / pivotstore);
                      		input[m][a] = input[m][a] * (1.000000 / pivotstore);
			        
			
		 	}
		


         /* lower triangular matrix */
	     for(a= m+1; a < sqLength; a++){
				
		double store = input[a][n];
		
		for( b = 0; b < sqLength; b++){
			
			/* either both negative or positive */
			/* whether it's negative, positive or zero, all of it is covered by this following formula */

				
			
				idMatrix[a][b] = ((-store / input[m][n]) * idMatrix[m][b]) + idMatrix[a][b];
		                input[a][b] = ((-store / input[m][n]) * input[m][b]) + input[a][b];
			     
              		}	
		    
                 }
		
	  n++;
          m++;
        }


while(c1 >= 0){
       /* store number below pivot */
	double pivotstore2 = input[c1][c2];
	for(a2 = sqLength-1; a2 >= 0; a2--){
		 /* scaling */
		 idMatrix[c1][a2] = idMatrix[c1][a2] * (1.000000 / pivotstore2);
                 input[c1][a2] = input[c1][a2] * (1.000000 / pivotstore2);
		 
	
	
		
	
	
      }
/* completely same process as lower triangular matrix, but in reverse */
    for ( a = c1-1; a >= 0; a--){
	double upstore = input[a][c2];
	for( b = sqLength-1; b>=0; b--){
				
					idMatrix[a][b] = (-upstore / input[c1][c2]) * idMatrix[c1][b] + idMatrix[a][b];					
  	                                input[a][b] = (-upstore / input[c1][c2]) * input[c1][b] + input[a][b];
                           
		   } 
		
	   }
    c1--;
    c2--;
  }
return idMatrix;

}
/* memory is precious, free it up */
void freeIt(double *done[], int mallocLength){
int x = 0;
        for( x = 0; x < mallocLength; x++){
                free(done[x]);
		/* prevent bugs and other nasty crashes*/
		done[x] = NULL;
        }
	
}


int main(int argc, char *argv[]){
	/* open 2 files, and have them read train and data */
	FILE *fp = fopen(argv[1], "r");
	if(fp==0){
		printf("%s", "error");
		exit(0);
	}
	/* null terminating character at the end */
	char traincpy[6];
	fscanf(fp, "%s", traincpy);
	if(traincpy[0] != 't' || traincpy[1] != 'r' || traincpy[2] != 'a' || traincpy[3] != 'i' || traincpy[4] != 'n'){
		exit(0);
		
	}
	int k,n,i;
	fscanf(fp, "%d", &k);
	if( k < 0 )
		exit(0);
	fscanf(fp, "%d", &n);
	if( n < 0 )
		exit(0);
	double** trainX = (double**)malloc(n * sizeof(double*));
	double** matrixY = (double**)malloc(n * sizeof(double*));
	double** matrixX = (double**)malloc(n * sizeof(double*));
	
	for(i=0; i< n; i++){
		trainX[i] = malloc((k+1) * sizeof(double));
		
	}
	for(i=0; i< n; i++){
		matrixY[i] = malloc(1 * sizeof(double));
	}
	for(i=0; i< n; i++){
		matrixX[i] = malloc((k+1) * sizeof(double));
		
	}
	for(i=0; i<n; i++){
	double num;
	int x;
		for( x = 0; x < (k+1); x++){
			fscanf(fp, "%lf", &num);
			trainX[i][x] = num;
			
			
                        
			if(x == k){
				matrixY[i][0] = num;
			} 
				
		}

	}
	/* put one's in first column, and shift every other column to the right */
	for( i = 0; i < n; i++){
	matrixX[i][0] = 1.000000;
	
	}
	int x = 0;
	for ( i = 0; i <n; i++){
		for(x = 1; x < k+1; x++){
			matrixX[i][x] = trainX[i][x-1];
			
		}
	} 
		
	
	

	fclose(fp);
        /* same process as above, only difference is that this file has n rows, and k columns */
	FILE *fp2 = fopen(argv[2], "r");
	if(fp2 == 0){
		printf("%s", "error");
		exit(0);
	}
	
	char datacpy[5];
	fscanf(fp2, "%s", datacpy);
	if(datacpy[0] != 'd' || datacpy[1] != 'a' || datacpy[2] != 't' || datacpy[3] != 'a'){
                exit(0);

        }
	

	int k2, n2, i2;
	fscanf(fp2, "%d", &k2);
	if( k2 < 0 )
		exit(0);
	fscanf(fp2, "%d", &n2);
	if( n2 < 0 )
		exit(0);

	double** matrixX2 = (double**)malloc(n2 * sizeof(double*));
	for(i2 = 0; i2 < n2; i2++){
		matrixX2[i2] = malloc((k2+1) * sizeof(double));
	}
	
	for(i2 = 0; i2 < n2; i2++) {
		double num2;
		int x2;
		matrixX2[i2][0] = 1.000000;
		for(x2=1; x2<(k2+1); x2++){
			fscanf(fp2, "%lf", &num2);
			matrixX2[i2][x2] = num2;
		}
	
		
	}	
	
	fclose(fp2);

double** tranX = transpose(matrixX, n, (k+1));
double** matrixtrainX = multiply(tranX, matrixX, k+1, n, n, k+1);
/* must use 2 original matrices since one original matrix shall be converted to the inverted form */
double** invertedX = invert(matrixtrainX, k+1);
double** inversexTran = multiply(invertedX, tranX, k+1, k+1, k+1, n);
double** Wmatrix = multiply(inversexTran, matrixY, k+1, n, n, 1);
double** result = multiply(matrixX2, Wmatrix, n2, k2+1, k+1, 1);
printPrice(result, n2, 1);
/* free all the double pointers or arrays */
freeIt(trainX, n);
freeIt(matrixX, n);
freeIt(matrixY, n);
freeIt(matrixX2, n2);
freeIt(tranX, (k+1));
freeIt(matrixtrainX, (k+1));
freeIt(invertedX, (k+1));
freeIt(inversexTran, (k+1));
freeIt(Wmatrix, (k+1));
freeIt(result, n2);
/* program successfully compiled! */
return 0;
}

